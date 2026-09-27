# How Burro got here

For a reader a year from now. Written on 25 September 2026, the evening Burro was first deployed, from the repository's own record: its history, [the decision records](adr/README.md) and what each guide says of itself. Add to it, and do not rewrite it. Every time is UTC.

## What was built, and in what order

| Day | What was built | Decision records |
|---|---|---|
| 23 September 2026 | [The plan](PLAN.md) and [its research](research/README.md). The licence registry and its gate. The engine, a made-up city to run it on, the API, the website and the source of the iPhone app. The design for [real data](design/london-data.md), and the first files fetched. The review desk. [The legal drafts](legal/README.md) | 0001 to 0017. A model stays at the edges (0002). Nothing typed is stored (0005). Rank places, never residents (0006). A made-up release to build on (0010) |
| 24 September | The first previews of London, of four measures at first. The first draft of its names. Four providers of a model, and none turned on. **The first push, and the first hosted fetch** | 0018 to 0028. A real release is served only with its evidence (0018). Age and households may be ranked on (0006, amended) |
| 25 September | A preview of a hundred measures and fourteen vibes. The panel. The hosted build of London. The guides to [refreshing London](refreshing-london.md) and [adding a city](adding-a-city.md). **The first deploy** | 0029 and 0030. A release is approved by its lock and carried in the image (0030). The proxy audit is dropped (0006, amended) |
| 26 September | **The website was given its look**: the map of a gentle game, with a rabbit in it. With it, the first screen as one box, the settings beside the answer on a wide screen, and the town of an area. The box sends what was added to a search, and no more. The reader reads a time in hours, an amount by the week and a walk. [The page on children](legal/access-by-children.md). **The founder then walked the website, and it was rebuilt to what they wrote**: two ways in to a search, the answer and a larger map after one, comparing areas as a headline, far less on the pages that explain, other words, and a rabbit who always moves. **That evening the founder walked it a second time, and it was rebuilt again**: a search that asks nothing, a visit as a third kind of search, less said on the first page, and a rabbit who cannot be stopped and is given a few seconds to be seen. **That night it was driven and measured whole**, and what it takes of a sentence was decided again where the words give no way. The sections on that day, below, have the order and the wrong turns | 0033 to 0042. The look, and what holds it (0033). A town is drawn by rule, and is no picture of the place (0034). The look gives way to the answer (0035). What the box sends (0036). The app is held to a copy of the website's colours and words (0037). What the reader reads (0012, amended). After the walk: how the words are written (0038), comparing areas is a headline (0039), a page that explains leads with a key (0040), and the look, the town and where things stand on the search page, each amended (0033, 0034, 0035). After the second walk: a search may be a visit (0041), the website claims no standard of accessibility (0042), the website applies what was read and asks nothing (0012, amended), people are told of who reads on the page the foot leads to (0023, amended), a visitor is not told that a vibe is a rough guide (0013, amended), and the look, the town, the search page, comparing, the pages that explain and the words, each amended again. That night: what the website never takes without being asked (0012, amended again) |
| 27 September | **The founder had walked the website a third time, late on the 26th, and it was rebuilt to what they wrote**: a result that shows each thing that was asked for as a name and a gauge, and says in no sentence why it fits; the source of every figure under the working of a result, and no longer beside it; a picture at each end of every gauge, one at each; a trade-off that is drawn as one thing weighed against another; three drawings that were missing; and a hop that is slower, lasts longer and throws soil. The section on that walk, below, has what was asked for, and what the three walks taught together | 0046. What a result shows, and where the source of a figure stands (0046). The look, the wait of a first search, how a vibe is said on a result, comparing, the key and the words, each amended (0033, 0035, 0013, 0039, 0040, 0038), and with them what is said of a source and of a figure that is missing (0014, 0024) |

## The hosted runs

| When | What |
|---|---|
| 24 September | The first push, and the first hosted fetch into the bucket. The first hosted run of the app's tests failed 47 of them. It was the first time they had been run |
| 25 September, 04:18 | Push. The backend passed. The app failed 4 |
| 13:54 | Push. The backend had one error: a copy of a repository that git was still doing upkeep in. The app failed 5, each over a value that a test held as written and a recording had since changed |
| 18:16 | Push. In the backend a new test started a tool with the hosted runner's own settings in its environment. The app failed 2, both tests older than a change to what is drawn |
| 19:07 | Push. **Every hosted job passed, for the first time** |
| 19:26 | The first hosted build of London was started. Its first build passed in 27 minutes, at the first try |
| About 19:45 | The website was deployed to Vercel and the API to Fly.io, with the made-up city. The website calls the API and no other host |
| 22:48 | The build of London with the traffic near homes was started. It passed whole in 54 minutes, and the release was approved and deployed an hour later |
| 26 September, 00:04 | The website's first build on London asked the API for the page of every area. After about ninety the API's machine fell behind, the host answered 503 for three minutes, and the build failed. The website stayed on the build before. A build now makes the first 24 pages of areas, and any other is made when it is first asked for |
| 00:17 | The website was built from London. Typed into it, a sentence was ranked, and its reasons did not come: they took four seconds on the API's machine, and the page waits five. Every figure of every area asked about had its band worked out over every area again. A release now works out where every area stands on every measure once, as it is made, and the reasons take a tenth of a second where they took eight tenths |
| 00:30 | The reasons took 0.7 of a second on the host, and a sentence typed into the website was ranked with its reasons a second and a half after the press. A model was then turned on, by hand: the service said that Gemini reads, the website told people so before they type, and a sentence was read in about two seconds |
| 00:35 | Push. It changed nothing of the review desk, and one test of the desk failed in the backend. The desk prints the line of a request once its answer is sent, and the test stopped the desk as soon as it had the answer, so the line was never printed. The test had passed on a runner ten times before. It now reads the line before it stops the desk |

In the runs of 13:54, 18:16 and 00:35 the test was at fault each time. For the first two no code that is shipped was changed. For the third the desk was changed by one word: it prints its last word at once, so that a desk that is stopped while a line is printed ends as a program that went well.

## Three kinds of fault that only a hosted run showed

| The fault | How it was closed for good |
|---|---|
| **Git's own upkeep, in the background.** After a commit git looks the repository over in a process it lets go of, and holds a lock meanwhile. A test that copied a repository listed the lock and then found it gone, in some runs only | Every git a test starts is started apart: it does no upkeep of its own, and reads no settings of the machine or of the person. A copy passes over a lock of git's. [conftest.py](../conftest.py), [test_git_is_started_apart.py](../tools/tests/test_git_is_started_apart.py) |
| **A value copied from a recording.** A test of the app held as written an id, a count or a hash that the service had made. Once the answers were recorded again, it held what nothing had made | A test reads such a value from the recording, and a guard fails a file of tests that holds one as written: [RecordedAnswersTests.swift](../apps/ios/BurroKit/Tests/BurroKitTests/Foundation/RecordedAnswersTests.swift) |
| **A hosted runner's settings, reaching a test.** A runner tells every step where its own files are. A tool under test wrote where it was told, so on a runner alone a test opened the runner's own file | What a runner sets is taken out of the environment before any test runs. [conftest.py](../conftest.py), [test_nothing_of_a_runner_reaches_a_test.py](../tools/tests/test_nothing_of_a_runner_reaches_a_test.py) |

[ADR 0020](adr/0020-the-tests-run-side-by-side.md), under "What was found", has each at length.

## What else went wrong, and what it taught

| What went wrong | What it taught |
|---|---|
| Two checks changed the first real build after it was built, to see what noticed. Four things did not | A real release is served only with its evidence beside it, and an image carries one only where its lock is committed. [ADR 0018](adr/0018-a-real-release-is-served-with-its-evidence.md), [ADR 0030](adr/0030-a-release-is-kept-approved-by-its-lock-and-carried-in-the-image.md) |
| No try at Village feel reached the founder's bar. Of the fifty areas each try put highest, 8, 24 and 25 read as villages, where the bar is 30 | A vibe may say that it is less sure than the rest, and is then never taken without a press of its own. [ADR 0013](adr/0013-vibes-are-the-centre.md) |
| The research said another city would reuse the pipeline as it is. Seven of the 43 sources that hold a receipt are London's alone. About a quarter of what the first plan rested on was partly wrong | Have somebody try to refute every claim before it is built on, and list the sources that are one city's own. [Adding a city](adding-a-city.md), section 5 |
| The first rule on logs let a hash of a spec be written. It was tightened twice in a day | A hash can be matched to a workplace by trying specs. Logging is a list of what may be written. [ADR 0011](adr/0011-nothing-is-kept-for-a-search.md) |
| On the first deploy the host's default builder refused to store the image it had built. The host also offers to deploy on every push | The guide names the host's own builder, and no push deploys. [Putting Burro on the internet](../deploy/README.md) |

## The day the website was given its look

26 September 2026. Written that afternoon, from the record of the day. When it was written nothing of the look had been pushed or deployed, and no hosted job had run on it.

| # | What was done, in the order it was done |
|---|---|
| 1 | Five looks were drawn, each a whole look built as a page, and with them a flow for a search: how the pages should work. Every one was drawn round a donkey |
| 2 | The founder chose one of the five, in paper, wood and browns. It was built: its colours, two faces, its drawings and a kit of parts |
| 3 | The founder said what the name means. The donkey went and a rabbit was drawn. The look was held back, to paper and ink with a drawing here and there, and built a second time |
| 4 | The founder saw both on the website, was asked what they wanted of a look, saw a sketch of what they answered, and chose another of the five, in full: Town Map, the map of a gentle game |
| 5 | The look was built a third time, from the ground up: twenty colours, a meadow in tiles, the box, 111 drawings written as text, the kit, and two faces. The founder chose the face of a sentence by eye, with three side by side on the website |
| 6 | With it: the first screen as one box with the settings beside the answer on a wide screen, what the box sends, what the reader reads, the app's copy of the website's colours and words, and the page on children |
| 7 | The search page was dressed in the look. Dressed, the first result of a phone ended at 994 px of a screen 844 high. The look gave way until it ended at 828 |
| 8 | The page was walked in a browser at two sizes, by pointer and by keyboard. What the walk found was mended, and eight things more were written down and left |
| 9 | The pages of an area, a comparison, a shared search and the pages that explain were dressed |
| 10 | The town was set beside the name of every result that has room for one. What the walk had found and left was mended on the search page, on the map, in a comparison and on the page a shared link opens |
| 11 | The decisions were recorded, and the guides brought to what was built. [The design of the look](design/look.md) lists what is still open |
| 12 | The town of a result was made whole, and the tests of the whole website were brought to the look. What was still to do was done, or written down with why it was left |

| What went wrong | What it taught |
|---|---|
| **The flow was written of the website as it had been two days before.** The trunk had moved on. Much of what the flow proposed the trunk had built already, or had tried in a browser and put aside | Say which commit a design is written against, and hold it to the trunk of that day. The flow was put aside, and the look was given one rule: the search works as it works on the trunk, and the look changes how it looks |
| **The look was drawn round a donkey, because nobody asked what the name meant.** "Burro" is the Spanish for one. Five looks and a first build held him, with his panniers | Ask what a name means before it is drawn. The founder said it in a line: "a play on words for the London Borough and a Rabbit burrowing into their home". A test now refuses a drawing of the donkey, or of anything that was his, by its name |
| **The look was turned down too far, twice.** The founder had asked that the game was not overdone, and the regulator names cartoons and gamification among what draws children to a service. So the look was held to paper first, and where there was doubt the quieter way was built. On the website it read as any quiet website | A look is judged on the page, by the person whose it is. Where there is doubt both ways are built, behind one line, and the founder chooses. What a regulation may ask is met by building each part so that it can be turned down, and not by building it faint ([0033](adr/0033-the-website-looks-like-the-map-of-a-gentle-game.md)) |
| **What the founder wanted of a look was asked last.** It took them ten minutes to say, and it settled the look | Ask first. Two looks were built that do not stand |
| **The look broke a rule of the website, and no part of it did.** Each part of the page kept to its own room. Together they stood the first result under the foot of a phone's screen | Measure the whole page, in a browser. What gives way to the answer, and in which order, is written down ([0035](adr/0035-the-search-page-is-one-box-and-the-look-gives-way-to-the-answer.md)) |
| **A face that was chosen for how well it is read draws a nought with a stroke through it**, and a page of rents and prices is a page of noughts | Set the real page in a face before it is chosen. What was given up with the face that was taken is written beside the choice |
| **Four things a person types every day were read wrongly, and a second sentence set back what had been set by hand.** "1 hour 15" was a journey of 15 minutes. None was new that day. Each was found by typing into the page | Use the thing as a person would, early. Then 3,258 sentences were typed against the reader, to find a wrong reading |
| **The app's check would have failed at the first colour the website changed**, and nobody ran its tests that day | The app is held to a copy of the website's colours and words until it is given the look, and the record says plainly that nobody has run its tests ([0037](adr/0037-the-iphone-app-is-held-to-a-copy-of-the-websites-colours-and-words.md)) |
| **The town of a result said what was untrue of its area.** It was drawn from the strip of its result, which holds what was asked for and two more, so every town had a part left blank and said of it that it was not known. The page held where every area sits, and the town was not handed it | A blank is for what is not known, and never for what was not asked for. A part is handed what the page holds before it is shown as finished |
| **The design of the website was true of the trunk and untrue of much of what was built**, for most of a day | A guide is brought to what is built in the change that builds it |

## The same day, once the founder had walked the website

26 September 2026, later that afternoon. Written as the rebuilding began, from what the founder wrote and from what was decided of it. So it says what was asked for and what that taught. What was measured of what was then built is in [the design of the website](design/web.md), sections 4.1 and 4.2.

| # | What was done, in the order it was done |
|---|---|
| 13 | The founder walked through the website in a browser, from its first page to its pages that explain, and wrote what they found |
| 14 | What they wrote was set beside what it would take, point by point, and with it a guide to how the words of the website are written: [the words of the website](design/words.md) |
| 15 | The website was rebuilt to it: where things stand on the search page, the settings, what Burro understood, comparing areas, the pages that explain, the rabbit, and the words of the page of an area |
| 16 | The decisions of that morning that the walk overturned were amended, each saying what was decided before, and three were recorded that had not been decisions until then |

What the founder asked for, in their words:

| Of | The founder wrote |
|---|---|
| What Burro is for | "The overall message of the app/product is to 'Find your area' weathe rbuying, renting, or just visitin , Burro will help you find a area to call your own." |
| The first page | "it is lacking a narative structure on the first page. The search journey is either - text search or slider/settings search, structure it this way, I want it clearer that a user can go down either path" |
| The page of results | "Map should be larger on the search result", and "Settings should be a 'refine search' collapsed section." |
| What was drawn to say a thing | "The dashed border is not understood to a user, please make solid", and "Unsure what unusal settings:6 assumed refers to. either show those or remove the section." |
| Comparing areas | "Compare function is great, make this more of a highlighted feature" |
| The pages that explain | "Methods is too much informtion, and probably of no value to a user", and "A key to the visuals/icons is valuable, and should be expanded." |
| The words | "Much of your copy in vibes is nonsensical, can you write copy in a manner that is more typical for a broad audience" |
| The rabbit | "the burrow bunnny should always be animated, ear twitching, sniffins, shuffling etc, he should add some movement and whimsey to the page." |

| What went wrong | What it taught |
|---|---|
| **The website was built and checked before its founder had walked it.** Every check passed: 5,063 tests, every page built and read, a walk in a browser at two sizes. The founder then asked for another first page, another page of results, far less explaining, other words, and more of the rabbit | A check holds a page to what was decided, and none asks whether that was the thing to decide. The person whose website it is walks a page as soon as it works, before the pages behind it are built on it. The day's own record said "Use the thing as a person would, early", of the reader of sentences, and the website was finished before it was done of the website |
| **What the founder had settled that morning, the founder overturned that afternoon.** The first screen as one box, the settings open beside the answer and a rabbit who sits still were each built as they were asked for. Walked, it was not plain that a search can begin either way, the map was too small beside the answer, and the rabbit was wanted moving | What is asked for of a thing nobody has used is a guess, the founder's as much as anybody's. A sketch and what the founder answered settled how the website looks. How it is used was settled by using it. A decision that is overturned within the day is amended, and says what was decided before ([0033](adr/0033-the-website-looks-like-the-map-of-a-gentle-game.md), [0035](adr/0035-the-search-page-is-one-box-and-the-look-gives-way-to-the-answer.md)) |
| **The words were written in the manner of these documents, as for a reader who knew the design, and no other reader had read them.** A page spoke of a recipe, a band, a part and a share, in sentences that each stood alone. [The design of the look](design/look.md) had listed them as words nobody had reviewed | Words that a visitor reads are written for a person who has not read the design, and are read by such a person before they are built on. What a sentence promises is not loosened so that it reads well ([0038](adr/0038-the-words-of-the-website-are-written-for-a-person-who-has-never-seen-burro.md)) |
| **A mark that was drawn to say a thing said nothing to the person it was drawn for.** A dashed edge stood for what was assumed, a chip counted six usual settings, and a label said that the words were read without AI. Each was true, and what the first two meant was said one press away, under the chips once they were opened out | A visitor has been told nothing. A thing is said in words where it is shown, or it is shown whole, or it is left out. A usual setting that nobody chose moves no area, so the chip that counted them told a person nothing they could use |
| **The pages that explain said all that is true, at full length.** On a phone the methods were 49,215 px long, and the page of vibes 27,524. The key to the drawings, which the founder called valuable, stood at the foot of the page of vibes | That a thing must be shown is no reason for it to stand in sight. What a visitor needs leads, and the working is folded under it, whole. What a licence or a promise asks to be seen stays in sight ([0040](adr/0040-a-page-that-explains-leads-with-a-key-and-folds-its-working.md)) |
| **What was best liked was hardest to find.** Comparing areas was the third of three small buttons at the foot of a result, and a bar that came once an area was chosen | What a thing can do is said before it is asked for. It is highlighted as a thing to do, and never as a verdict: nobody wins a comparison ([0039](adr/0039-comparing-areas-is-a-headline-of-the-website-and-nobody-wins-a-comparison.md)) |

## That evening, once the founder had walked it a second time

26 September 2026, that evening. Written as the second rebuilding began, from what the founder wrote and from what was decided of it. So it says what was asked for and what that taught. What was measured of what was then built is in [the design of the website](design/web.md), sections 4.1 and 4.2. When it was written nothing of the day had been pushed or deployed.

| # | What was done, in the order it was done |
|---|---|
| 17 | As it was first rebuilt, the first result of a desk began at 899.5 px of a window 900 high: a line in whole sentences, the fold of the settings and the line that says areas can be compared had each taken their room at once |
| 18 | The website was walked in a browser, by one way through it after another, and what each walk found was mended. The first result of a desk came back into sight, at 689. Deep search came to make a search by its button alone, the rabbit came onto every page, and the page came to be in the order it is drawn in |
| 19 | The words of the service were written again for a person who has never seen Burro, as the words of the website had been. The catalogue moved for it, from 15 to 16 |
| 20 | The founder walked the website a second time, that evening, and wrote fourteen points |
| 21 | What they wrote was set beside what it would take, point by point, with four things decided for them, each theirs to overturn |
| 22 | The website was rebuilt to it: how a search is made, the settings, a result and a comparison, and what goes from every page. With it, a visit in the service, the iPhone app, and the records and the designs |

What the founder asked for, in their words:

| Of | The founder wrote |
|---|---|
| A comparison | "Compare areas needs a back step, how do I get back to my search?" |
| The rabbit | "remove the pause button for the rabbit, for accessibility we will rely on users having motion turned off in the browser" |
| The words under the box | "remove how your words are handeld from the home page search. this is overkill" |
| The first page | "Change describe the life you want to - tell me whats important in your space. Then give more of a discriptive explaination on what a useful sentence should be." |
| Deep search | "on deep search you have duplicated the explainer text, remove the explainer copy from the settings section, and rename it to Space requirements." |
| A visit | "Add a visiting option under renting or buying, again, this should accomodate people who are looking where to get a hotel etc." |
| A vibe that is less sure | "remove the concept of rough guide, we don't want to pass this on to a user" |
| What is switched on | "it is unclear what the select state of the toggle is, also there is toomuch layout shift when toggling" |
| A result | "remove the 'each little town' disclaimer on the ranking cards", and "ensure the gauges all line up vertically so that a user can scan downwards with ease" |
| The statement of accessibility | "get rid of the accessibility tab. Overkill" |
| What Burro asks | "When running a search, don't ask the user to add anything, assume they want it to be added and just present the results. Is this due this demo not having gemini?" |
| The wait | "even if not needed, create a few seconds load time to allow the bunny jumping into a hole animation to appear and take center stage" |

| What went wrong | What it taught |
|---|---|
| **A rule was taken for a fault.** That Burro asks before it applies what it is not sure of was decided by the founder two days before, and is written in two records. Walked, it read as a part that was missing: the founder asked whether it was for want of a model | A rule that stands between a person and their answer is judged at the screen, by the person it stands in front of. The cost of asking had been counted in presses: ten, and then one. The cost of not asking is a wrong reading that reaches the ranking, and the record now says which, how often where it was measured, and what holds it ([0012](adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md)) |
| **What was held to be nobody's to give up was the founder's.** The first rebuilding held that whatever moves without end can be paused, because the website said that it aimed at a standard of accessibility. So a button was built beside the rabbit. The founder took the button away, and the statement with it | A promise that is made to a visitor is kept whatever a critique says: that a figure has its source, that nothing typed is kept. What the website says of itself is a claim, and the founder's to make or to take back. What is written down before a rebuilding says which is which ([0042](adr/0042-the-website-makes-no-claim-of-a-standard-of-accessibility.md)) |
| **Four things that were true were each one too many.** The line on how words are handled, the label of a rough guide, the line that says a little town is no picture of the place, and the sentences at the head of the settings. Each was asked for by a record, and each was written as the guide to the words asks | That a thing is true and well said does not settle where it is said, or how often. A caution that stands on every card is read as doubt, or not read. Each that was taken away was there to keep something from going wrong, so the record of each says what was given up, and what holds it now |
| **The first page promised what no search could be.** "Whether you are buying, renting or just visiting" stood under the heading for half a day, while a search was to rent or to buy and nothing else | A sentence of the first page is a promise of what a person can do. What it promises is built in the change that says it ([0041](adr/0041-a-search-may-be-a-visit.md)) |
| **The way in was made a headline, and the way back was forgotten.** A comparison was reached from every result, and nothing at its head led back to the search | A journey is walked there and back before it is called done |
| **Deep search said what it is twice**, once under its tab and once at the head of its settings. Each was written for its own part of the page, and the test that reads the website's words as one voice holds that one thing has one name, and not that a thing is said once | A page is read from its head to its foot, as a visitor reads it, before its founder reads it |
| **"Nothing moves under a press" was held of what a style does, and not of what a press brings.** A thing that was switched on drew its slider, and everything under it went down by as much | A rule of layout is held by measuring in a browser where a thing stands before a press and after it. A test that reads a style sheet sees no slider that was not there |
| **He was seen for a few frames.** A least time on stage for the rabbit had been weighed that morning, and put aside so that the answer came as soon as it could | What is quickest was taken for what was wanted. The founder wanted him seen, and the answer still comes first once it is shown |
| **The records and the designs fell behind the website within hours.** What was mended that afternoon changed where things stand on the search page, and no record and no design was changed with it. The founder walked a website that its own design did not describe | This page had said it that afternoon: a guide is brought to what is built in the change that builds it. A change that mends is such a change |
| **The catalogue moved for words alone, and the release of London that was approved was no longer one the service serves.** A release carries the name of each measure, so to write the names again was to change what every release must hold | A change to what a release carries is a change to every release. London is built again in the change that moves the catalogue, or nothing is deployed from it until London is built ([the guide to data builds](data-builds.md)) |

## The same day: accounts, as groundwork

26 September 2026, that evening, while the website was being rebuilt to the founder's second walk. Written as accounts were built, from what the founder wrote, from the design, and from the code as it was committed. **Accounts are built, and are off until they are turned on. Nothing of them has run on a host.** [The design of accounts](design/accounts.md) says what is built, and [the guide to deployment](../deploy/README.md#turning-accounts-on) what stands before they are turned on.

What the founder asked for, in their words:

> We will also need to lay the ground work for a user login, account creation, security etc. Hardening with proper logging etc. If those can be added in parallel please do so. We can keep it simple with magic link login etc. I'd prefer good securirty with mininal overhead. We'd need to store user preferences/previous searches etc and re-present this etc.

| # | What was done, in the order it was done |
|---|---|
| 1 | A design was written, and with it a list of the written promises that it changes: that the server keeps nothing for a search, that Burro builds no accounts, and that the service has no database |
| 2 | The design went through a review of its security, before anything was built. Two things were found, and both are in the design: a link that somebody else sent must not sign a person in to that somebody's account unseen, and the address of a client is believed from the website alone |
| 3 | It was built in the service and in the website, and the records and the guides were written with it |
| 4 | In the service the contract came first: seventeen routes were declared with what each takes and gives, and none was served, so that the website could be built against them. Then the address, the token, the file, the limits, the settings, the sender, the name of a search, and last the rules of signing in |
| 5 | The decisions were recorded, and the three promises amended, each saying what was decided before ([0043](adr/0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md), [0044](adr/0044-a-person-who-has-signed-in-may-keep-a-search-and-what-is-kept-is-the-spec-and-never-the-words.md), [0045](adr/0045-the-service-has-a-database-one-file-for-accounts-and-what-they-keep.md), and [0005](adr/0005-raw-prompts-are-never-stored.md), [0011](adr/0011-nothing-is-kept-for-a-search.md), [0023](adr/0023-what-is-typed-goes-as-typed-and-people-are-told.md) and [0032](adr/0032-calls-to-a-model-are-capped-for-the-whole-service.md)) |
| 6 | What was built was tried hard, on a copy on one machine and on no host. Four things did not hold, and each was mended with a test that failed before it was: a page that the browser kept showed an account after its person had signed out, how long an answer took told that an address had asked for a link lately, a search that was taken away stayed in what is written beside the file, and ten requests from anybody stopped everybody from signing in. [What could go wrong](design/accounts-threats.md) says each, at ways 58, 28, 44 and 33 |
| 7 | Accounts were brought to the website as the second walk left it, and the two were walked together in a browser, with accounts off and then on |

| What was found | What it taught |
|---|---|
| **The plan had bought accounts from another company, with three ways to sign in.** The founder asked for a link by email and "mininal overhead". What was built adds one company, which sends the mail, and no dependency: a database, randomness, hashing and HTTPS are in the standard library | A plan that was written before anything was built names what could be bought. What is asked for once the thing exists is often less |
| **What was weakest was found by reading the design for what could go wrong**, and not by a test. A link that signs a person in as it is opened passes every test of signing in | Have a design read by somebody who means it harm before it is built. What they find is written into the design, and then held by a test: [what could go wrong](design/accounts-threats.md) keeps the list, and says of each way in what nothing holds |
| **The design asked that the website and the service stand under one domain, and nothing that was built asks it.** A browser asks the routes of accounts of the website, and never of the service. What needs a domain is the mail, and the name a link leads to | A condition is written down with what it is for. One that is written without is kept after its reason has gone |
| **Two risks were given one number**, in a list that was added to for accounts and for the second walk in one evening | A number that others cite is given out in one place, as the numbers of the decision records are held by a test. The risks of accounts were numbered again, after the risk of the second walk |
| **The launch checklist was not given a fifth stage.** A test holds its tasks to be counted in four stages | What stands before accounts are turned on is lettered, and stands after the four stages. A count that a test holds is a promise to whoever adds to it: say beside the count how a thing is added |
| **What was tried found what no test had.** Each of the four faults passed every test that had been written for it, and the design said nothing of any: of a page that a browser keeps, of an address that is sent no letter, of what is written ahead of a file, of a request that names no client | A design is read for what it does not say. Whoever tries what was built writes the test that fails first, and then the line of the design that was missing |
| **One number came to mean two decision records**, a visit and accounts both, and accounts had been recorded twice over | One decision has one record, and one number. What the second record of accounts said that the first did not was brought into the first, and the second is gone. The test that holds the numbers failed, which is what it is for |
| **The entry of accounts was measured against a name board of four pages, and the board came to hold three that evening.** Its comments and its record gave figures that were no longer so, and what it was built to save, a line of the board on a phone, was saved already on all but the narrowest | A figure that was measured says what it was measured against, and is measured again when that changes |
| **A search that is a visit could not be kept.** The name of a kept search had a word for renting and for buying, and the third kind of search was built that same day. No test failed: the test of every kind of home found that a visit has none, and held nothing of it | A list that is drawn from every value of a kind holds a value that is added later. One that names its values holds those it names |
| **The app's generator stopped at the first route that answered 202**, and behind that at a route that is no `GET` or `POST`, and behind that at a record of accounts that bore a name of the app's own | A tool that stops at the first thing it has no rule for says one thing at a time. What it makes of the contract as it stands is now held where no Mac is needed, in `make ci` |
| **Three promises were changed in one evening**, each of which a visitor had been told | A promise that changes is amended in the change that builds it, and says what was decided before. None of the three was changed for a person who has not signed in, and all of accounts is off until the founder turns it on |

## That night, once the website had been driven

26 September 2026, that night. Written as what was found was being mended, from what driving the website and the service showed, and from what was measured. When it was written nothing of the day had been pushed or deployed.

| # | What was done, in the order it was done |
|---|---|
| 23 | The website was driven as a person uses it, at the size of a desk and of a phone, and the service sentence by sentence, with every check of the repository run beside them. Every check passed. What did not hold was written down, each thing with how to see it |
| 24 | What the website takes of a sentence was decided again, where the words give no way: neither way of a rule that leaves areas out, and neither of a thing that runs two ways ([0012](adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md), as amended that night) |
| 25 | The website as it stands was measured in a browser at both sizes: where the first result stands after twelve searches, the page of every area, the pages that explain, the bar of areas, the map, and what moves under a press. The designs and the records were brought to what was measured |

| What was found | What it taught |
|---|---|
| **An area was left out on a guess, the evening it was decided that none is.** Where the words gave no way, the website took more of what the name of a thing says. Of a rule for an area, more is to look only there: "Leafy and quiet, near Gorsebeck" ranked one area of 22 | A rule is held of what it means, and not of the word it was written in. The test held that no limit leaves an area out, and none held it of a rule for an area. Whatever leaves areas out is never taken on a guess |
| **A person who typed 40 minutes was given 45, and told that they gave no number.** A time that stood after its place was not read, in twelve of 29 plain ways of saying it. It was so before that day, and began to matter that evening, when the website came to take every offer unasked | What is safe as an offer is not safe once it is applied. When what stood between a reading and the search goes, every reading is read again for what it does with nobody to catch it |
| **A word for a smart area was ranked on by what follows household income.** The record of household income had that measure offered and never applied. It was never applied by the service, and the website took the offer | A promise that rests on a person choosing is found and weighed again when the choosing goes. It is the founder's to decide, and the record now says that it is open ([0028](adr/0028-household-income-is-shown-and-never-ranked-on.md)) |
| **Two pages told a visitor for an evening what was no longer so.** The methods and the key to the drawings said that Burro asks, and adds nothing until a person chooses. The terms and the privacy notice had been brought to the change, and the website's own pages had not | When a rule of the product changes, every page that says the rule is found by what it says, in the change that changes the rule |
| **The designs put their measuring off in seventeen places**, until the website was whole, and said so still once it was | What is put off is written with what ends the wait, and is done in the change that ends it. A figure that was measured says when, and of what |
| **Measured whole, the phone held less than was thought.** After a plain search the first result had 6 px to spare, where it had 16.5 that afternoon, and after five of twelve searches it ended under the first screen. Three pages of an area were wider than the window, by one line that was set not to break | A rule of where things stand is measured on every page of a kind, and after every change that adds a line. One page of 24 measured is a sample |
| **One thing had two names on one screen**: "Space requirements" over the settings, and "the settings" in the sentence over them and on the button under them | A name that changes is changed wherever the thing is named, and the test that holds one name for one thing reads the whole page |

## Late that night, once the founder had walked it a third time

26 September 2026, late that night, and the day after. Written as the third rebuilding began, from what the founder wrote and from what was decided of it. So it says what was asked for and what that taught. What was built of it, and what was measured of it, is in [the design of the website](design/web.md), section 4, and in [the design of the look](design/look.md). When it was written nothing of the look had been pushed or deployed.

| # | What was done, in the order it was done |
|---|---|
| 26 | The founder walked the website a third time, late that night, as the second rebuilding had left it, and wrote of the hop, of a result, of the gauges and of three drawings that were missing |
| 27 | What they wrote was set beside what it would take, point by point, with four things decided for them, each theirs to overturn: how long a first search waits, what a trade-off is drawn with, what the mark of "approx data" is, and that a trade-off keeps its sentence |
| 28 | The website was rebuilt to it: the hop, the drawings, a result, and every gauge that stands on another page, with the key to the drawings. What a result shows was recorded, and the records and the designs that the walk overturned were amended, each saying what was decided before ([0046](adr/0046-a-result-shows-what-was-asked-for-as-a-name-and-a-gauge-and-the-source-of-every-figure-stands-under-its-working.md)) |

What the founder asked for, in their words:

| Of | The founder wrote |
|---|---|
| The hop | "slow the hole hopping animation down a bit and make it last a tad longer, make soil flick up as it burros" |
| The ends of a gauge | "good job with the gauges on the ranking cards, but there is more refinement needed. show only one example of house or flat type at either side of the gauge, this will help add space." |
| The words under a gauge | "remove the explainer text under the gauges. we dont need that level of detail. just show the incomplete data icon and simple text of 'approx data'" |
| Why an area fits | "Remove the why it fits section, again too much detail, ideally for the break down, we need the info to be title of what was asked for, the visual gauge, and where relevent, the approx data call out" |
| The key of a source | "the source's key should just exist under the show the working section we dont need it at the summary high level card version. Again, we don't need to over complicate and bloat with too much info." |
| A picture at each end | "Add any icon to the relevent gauge, for example, you have an icon for leafy and calm, but they are not in next the relevent gauge, where a gauge may exist, ensure they have a opposing icons for each side of the gauge." |
| The trade-off | "The trade of section is important, the icon of a red arrow doesnt make sense, and the section could stand out a bit more visually." |
| Three drawings | "Create visuals for brands near by, air and noise and recorded crime" |

| What went wrong | What it taught |
|---|---|
| **A result said everything it knew, and every word of it was true.** With each gauge stood where the area sits, in words, and what the band rests on. Under the gauges stood a reason in a sentence and a trade-off in another, and after each sentence the key of its source. Measured that night, a result was 491.5 to 786 px high on a desk, and no page of results was within the three screens its design allows | A result is read at a glance: what was asked for, and how the area does on it. What Burro knows beyond that is the working of the result, which is one press away, whole. The founder's words for the rest were "too much detail", twice, and "bloat" |
| **A gauge and the words with it said one thing twice.** "Around the middle" stood with five steps that had a peg on the third. The words had been added so that no drawing was left to speak for itself | Where a drawing says a thing at a glance, the words that say it again are for whoever cannot see the drawing, and a screen reader is told them. What is taken from sight is not taken from what is heard |
| **Where a source stands was taken for the promise itself.** The promise is that every figure traces to a fact with a source and a date (rule 6). The design met it with a key after every sentence of a result, and held that nothing is ever taken off a result | A promise says what must be so, and not where on a page it is shown. Where a thing stands is the founder's to move, and what holds the promise moves with it: the source of every figure of a result stands under its working ([0046](adr/0046-a-result-shows-what-was-asked-for-as-a-name-and-a-gauge-and-the-source-of-every-figure-stands-under-its-working.md)) |
| **A drawing was made, and was not drawn where it says most.** The small drawing of a vibe stood on its chip and on the bar of its group, and not beside its gauge. A vibe that runs between two named ends had a picture at each, and a vibe that runs one way had none | A drawing that the website has is drawn wherever its thing is shown. A rule of the look is tried on every gauge, and not on the first that was built |
| **Three groups of the settings stood under a plain box.** A drawing is chosen by the family of vibes a thing belongs to, and the settings show brands nearby, air and noise and recorded crime apart from every family | A rule that always has an answer hides where it has none of its own. What falls to the blank drawing is looked at, part by part |
| **The mark of a trade-off was a red arrow, and said nothing.** It was drawn in poppy, which is the colour of the edge of a fault | A mark is a drawing of what the thing is, and a trade-off is one thing given for another. Red says danger, and what an area gives up is no danger |
| **The hop read as hurried.** A round of it was a second. It had been looked at frame by frame, and timed by software, and the design of the look had said for a day that nobody had watched anything move | What moves is judged by watching it move, by the person whose website it is. A still frame does not say how fast |

### What the three walks taught together

**Each time, the founder kept the pictures and took words away.**

| Walk | Kept, or asked for more of | Took away |
|---|---|---|
| The first, on the afternoon of 26 September | A rabbit who always moves. The key to the drawings, which was to lead its page and to hold more. Comparing areas, as a headline. A larger map | Most of what the pages that explain held in sight. The label that said who had read the words, and the chip that counted the usual settings. The dashed edge, which was a mark that needed words |
| The second, that evening | A few seconds of every first search, for the rabbit to be seen in. The gauges of a result, which were to stand in one column | The words under the box, the sentences at the head of the settings, the label and the sentence of a rough guide, the line that says what a little town is, the statement of accessibility, and every question Burro asked |
| The third, late that night | A picture at each end of every gauge. Three drawings that were missing, and one for the trade-off. A longer hop, and soil from the hole | The words under a gauge, what a band rests on, "Why it fits", and the key of a source on a result |

| What the three walks showed | What it taught |
|---|---|
| **Every sentence that went was true, and most of them kept a promise.** Each had been put in sight so that a promise was kept where a person looks: that a figure has its source, that a little town is no picture of the place, that a band rests on part of what it needs, that a person is told who reads what they type | A promise is kept by what is so, and by what a person can reach. It is not kept by standing between a person and their answer. Of each thing that is taken from sight the record says what it was there to hold and what holds that now |
| **What was built erred the same way each time, towards saying more.** Where there was doubt a sentence was added, because a sentence can be shown to be true and a gap cannot | Where there is doubt between showing more and showing less, less is shown, and the rest is kept one press away, whole. It was written down as a direction after the third walk. It could have been after the first |
| **The founder asked three times for less to be said, and never for a thing to be untrue.** No walk asked that a figure lose its source, that a guess be shown as known, that what is not known be drawn as nought, or that a place be given a verdict | What the product promises and how much a page says are two matters. The first holds whatever a walk asks. The second is the founder's, and is settled by walking the page |
| **No drawing was asked to go, in three walks, but one that said nothing or said a thing twice**: the dashed edge, the red arrow, and the second house of a pair at the end of a scale | A drawing earns its place where it says what a thing is, at a glance. One that has to be explained is a word that was drawn |
| **Each walk was of the website that the walk before it had made.** The gauges were praised on the third walk because they had been set in one column after the second, and only then was it seen that the words under them were not needed | One walk does not find what the next will. A page is walked again once it is rebuilt, by the same person |
| **What a picture cannot say is still said in words, and in few.** A gauge cannot say that the figure behind it is not whole. The founder gave the words for it, "approx data", and asked for a mark beside them | Words are for what no drawing can carry: a name, a figure, a source, and that a thing is not known. The guide to the words says so since ([the words of the website](design/words.md)) |

## The day after, once the website was measured as it stands

27 September 2026. Written from what a browser showed of the website since the third walk, at 1440 by 900 and at 390 by 844, on the made-up city, and from what the guides said beside it. It is of the documents and of what was measured, and of nothing else that was mended that day. [The design of the website](design/web.md), sections 4.1, 4.2 and 9, has every figure.

| What went wrong | What it taught |
|---|---|
| **The walk that the README sets out could not be followed.** One row asked for a journey to be made firm after a row that had begun a search which holds none. Another said that a sentence ranks the areas, and since the service says what waits for a person it ranks none. Each row was true the day it was written, and the table said of itself which rows had been walked | A walk that is written down is a check that nobody runs. It is walked again, in its order, in the change that changes what a search takes, and the order it is written in is the order it is walked in |
| **Two designs gave the figures of a result that was measured before its page had changed.** They said that on a phone a first result of four gauges ends under the first screen. On the website as it stands it is whole after every search that was measured, with 84.5 px to spare at the least | A figure is of the page a visitor meets. One that is measured of a part says so, and is measured again once the part stands on its page |
| **Four documents said where a line stands, and none of them had looked.** The line of what was left out of a search stands over what Burro understood, since it changes what the ranking means, and they said under | Where a thing stands on a page is read from the page |
| **The legal drafts marked as not built what had been built for two days and more**: that the service turns one provider on for nobody, the census table of an area, the measures of age and of households, and a vibe that counts recorded crime. They had been brought to every change of the website and to accounts, and to no other change of the service or of a release | A draft that promises is read against the code whenever a part that it names is built. Until it is, the list of what it is behind in stands at its head: [the legal drafts](legal/README.md) |

## What the project would do again, and what it would do otherwise

| Again | Otherwise |
|---|---|
| Build on a made-up city that cannot be taken for a real one. Three parts were built to one contract before any real file was held | Hold the measures against the real city sooner. The plan says that nothing seen on the made-up city says how the product will feel on London |
| Write a decision down with its reason on the day it is made. Thirty records in three days are why this page could be written | Run the hosted checks from the first day. The app's tests were first run a day after they were written, and it took four more pushes to reach no failure |
| Say in every guide what was tried and what was not | Say it in one place. "Never run on a host" stood in many guides, and each went stale in one evening |
| Hold a promise by a test, and say plainly where nothing holds it: [the picture of the whole](architecture.md) | Read from a recording whatever the service made, from the first test |
| Write a drawing as text, and make the picture from it: a change to a picture is then read as a change to a line, and a test holds every picture to the colours of the look | Ask what a name means, and what a person wants of a look, before anything is drawn |
| Build each part of a look so that one line turns it down, and hold by a test that it does | See a look on the website before a second is built on the first |
| Amend a decision on the day it is overturned, and keep what was decided before beside what stands | Have the founder walk the first page that works, before the pages behind it are built |
| Say in the record of a thing that was taken away what it was there to hold, and what holds that now | Tell a promise to a visitor from a claim of the website's own before a rebuilding begins, and ask the founder which of the claims they hold to |
| Have the founder walk the website again once it was rebuilt to their words: the second walk found what the first could not | Bring the records and the designs to the website in every change, the changes that mend among them |
| Drive the whole as a person uses it once every check has passed: every check passed, and what was driven still found what did not hold | Measure the whole website in a browser before a design says where things stand, and again after every change that adds a line over the answer |
| Have the founder walk the website a third time: each walk was of the website the walk before it had made, and found what could be seen only then | Begin with less in sight. Show what was asked for, and keep the working one press away, before the founder has to ask for it to go |
| Keep whole, one press away, whatever is taken from sight, and say in its record what holds the promise it kept | Ask of each sentence that stands beside a drawing whether the drawing says it already |
