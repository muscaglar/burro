# The panel: how a change reaches what people see

Status: designed on 2026-09-25, before it was built. Section 8 says what is built. It rests on AGENTS.md rules 5 to 9 and 13, ADRs 0002, 0006, 0013, 0026 and 0029, [the contract](contract.md), sections 2.3, 2.8 and 3.2, and [the desk](desk.md), which it is part of.

The panel is where one person looks through what Burro presents, renames it, and adjusts how it is worked out. It is the review desk, with more to it: the same server on the person's own machine, one more page, plain files. **Nothing a person does at the panel changes what is served. A build does, and a build is made on purpose.**

## 1. What a release carries today, and what core holds

| | A release carries it | Core holds it in code | Core refuses a release that differs |
|---|---|---|---|
| A vibe: its name, its ends, what it cannot see, its recipe | Yes, whole, in `catalogue.json` | Yes, in `TAGS` | Yes: `vibes_match_core`. A band is held to core's recipe too, and not to the release's: `raw_matches_recipe` |
| The label of a measure | Yes, in `catalogue.json` | Yes, in `FEATURES` | Yes: `catalogue_matches_core` |
| The table of brands | No. Each measure says in its `definition` which chains it counted | No. It is `brand_tiers.toml`, data of the pipeline's | No |
| How many sales a price needs | Each price says how many it rests on | Yes: `FEWEST_SALES`, a floor | Yes, below the floor |
| The margin on a firm budget, the numbers of the estimate of a journey | No | Yes: `rank.py`, `estimate.py` | It has nothing to refuse |
| How near is near: 800 m | No. The label of each measure says it | Yes, in the labels, and in each step of the pipeline | Yes, by the label |

So a release already has a place for a recipe and a name, and core will not yet let either differ from its own.

## 2. The smallest change to core

One change, reviewed as one, with its tests. `rank()` is not touched, and no id moves.

| Rule | Today | Then |
|---|---|---|
| `vibes_match_core` | A vibe of a release is core's, to the letter | It is core's but for what a person may adjust: the hundredths of its parts, its name, the names of its ends, and what it cannot see after the first line. Its id, family, shape, meaning, parts and the end each part is read from are core's. It is held to `checked_recipe()`, as core's own are |
| `raw_matches_recipe`, `sources_are_stated` | Read core's recipe | Read the recipe the release carries. `tag_raw()` is handed the recipe |
| `catalogue_matches_core` | A measure is named as core names it | Its label and its short label may differ. Everything else of it is core's |
| A name a person gave | | Holds no word that no sentence may say, no figure and no word for a group of people. A measure that counts residents still ends ", Census 2021" |

What a recipe is held to does not move: it sums to 100, no part is 60 or more, a part that counts residents is read from its high end and no part is over 40 beside it. Since 2026-09-25 the parts that rest on the conservation areas come to under 60 between them, so that their publisher's file never places an area alone. **No part is added, taken out or turned round by a change.** So no recipe can come to read a census figure that it does not read today, and none can read one from its low end.

## 3. The file of changes

One file for each reviewer, among the decisions of the desk's data: `decisions/changes/r1.jsonl`. It lies there so that the second copy the desk keeps of every decision holds it too. It is plain text, one change a line. A line is never changed and never removed. It is written as it may be committed: it says the day and never the hour, and the reviewer by a label and never by a name.

| Field | Holds |
|---|---|
| `n` | The number of the line in its file, from 1 |
| `on`, `by` | The day. The reviewer: `r1` is the founder |
| `what` | `recipe`, `name`, `cannot_see`, `label`, `brand`, `number`, `flag`, `leave_out` or `take_back` |
| `of` | What is changed: the id of a vibe, of a measure, of a chain or of a number. Of a flag: `figure/AREA/MEASURE`, `band/AREA/VIBE`, `name/AREA` or `border/AREA` |
| `was`, `now` | What stood before, and what stands now. Of a recipe, every part with its hundredths. A flag holds neither: **no figure of a place is ever written in the file** |
| `why` | The reason, in the person's words. One line of plain text, 500 characters at most. It is never empty |
| `takes_back` | Of `take_back`: the `n` of the line it takes back. Of every other line, `null` |

```
{"n":1,"on":"2026-09-25","by":"r1","what":"recipe","of":"family_amenities","was":{"school_primary_nearby":40,"play_space_proximity":35,"park_proximity":25},"now":{"school_primary_nearby":20,"play_space_proximity":47,"park_proximity":33},"why":"A park and a play space say more of a family's week than the count of schools.","takes_back":null}
{"n":2,"on":"2026-09-25","by":"r1","what":"take_back","of":"family_amenities","was":null,"now":null,"why":"It put the centre of town first. Back to the recipe as it was.","takes_back":1}
```

**Which line stands.** For one reviewer, one `what` and one `of`: the last line that no later line takes back. To take a taking back back puts the line in place again.

**Two reviewers.** Each writes a file of their own. A build is given one file, the founder's. Another reviewer's line is a proposal: it is kept, shown in the history, shown beside the founder's where the two differ, and never built.

## 4. How a build takes it

1. A person keeps a change at the panel. The line is on the disk, and in the kept copy, before the panel answers.
2. `make desk-publish` makes the copy of the file that may be committed, byte for byte, and hands every reason back to be read. The copy is committed. `make preview ARGS="... --changes gazetteer/london/decisions/changes/r1.jsonl"` builds from it, and from no file the repository does not hold: section 9. With no `--changes` a build is byte for byte what it is today. A hosted build of London is given the place the copy is committed to, with `--published-changes`: where the repository tracks a file there it builds from it as a build by hand does, and where it tracks none it builds as it did.
3. The build reads the file whole before it opens a publisher's file. A line it cannot read, a change that breaks a rule, and a change whose `was` is not what stands today each stop the build. It says the number of the line and the rule, and never what the line holds.
4. It names the file in the lock by its hash, as it names a draft of names, and the manifest of the release says the same hash. So a release says which changes it was built with, and core holds the lock to it.
5. It applies the lines that stand, and the release carries what was decided. `build.json` lists each line that was applied, by its number. `burro-release check` and the API hold the release to every rule, as any other.

| `what` | What a build does | What a person sees before it is kept |
|---|---|---|
| `recipe` | The vibe of the release has the new hundredths, and every band of it is worked out with them | How many areas change band, the areas that rise and fall most, and the first ten of three searches, before and after |
| `name`, `cannot_see`, `label` | The vibe or the measure of the release has the new words | The words, before and after |
| `brand` | The table of tiers is read with the change laid over it, and the measures of the chains are worked out again | The table, before and after. What moves is known only once it is built: the panel holds no file of places |
| `number` | Section 6 | Section 6 |
| `leave_out` | Not yet. The file has the line, and no build applies one: a figure a person left out needs a state of its own in the evidence, which is a change to the contract, to the API's words for a missing figure and to the website's types. A build that is handed one stops. So the panel does not offer it, and a figure is flagged | |
| `flag` | Nothing. It is listed for a person | |

## 5. What the panel never does

| Promise | How it is kept |
|---|---|
| A figure is a publisher's | No route takes a figure. A person may flag one, or leave one out of a build |
| A missing figure is never filled in | To leave a figure out makes it missing. Nothing makes one |
| Ethnic group, religion and country of birth are ranked on nowhere | The panel shows no census table and no income. A slider is of a part a recipe already holds. No route adds a part |
| Nothing lets a person ask for fewer of anyone | No route turns a part round. `checked_recipe()` refuses it in the build too |
| The panel holds nobody's search | The three searches of the preview are written in `tools/desk/panel/searches.json`. The founder's own sentence is case `whole-035` of the reader's evaluation set, by their consent |
| The server is on this machine alone | It binds to `127.0.0.1`, as the desk does. A test holds it |

## 6. The numbers a person set by judgement

**What is built is the list, and no more.** `GET numbers` lists each number with what it is today, its unit and where it is, so that a person can see them in one place. None is changed at the panel yet, and a build that is handed a line of the kind `number` stops. The table says how each would reach a release, and what that would take.

| Number | Where it is | How a change reaches a release |
|---|---|---|
| How many sales a price needs | `FEWEST_SALES` in core is the floor, 10. The pipeline reads it | A build would take a larger number from the file, and leave out a price that rests on fewer. The release carries it: each price says how many sales it rests on. A smaller number is refused: a figure of a few sales would say what one home sold for. Not built: the step that works a price out states the number in its method, so the number has to reach the step and its evidence together |
| The margin on a firm budget. The numbers of the estimate of a journey | In core: they are arithmetic, and no data of a release | A release would say them in its manifest, under `judged`, only where a build was given a change of one. `rank()` would read the release's number where it says one, and core's where it says none. So ranking is still a function of a search and a release. Not built: it is a change to `rank()` and to the manifest, which is a change to the contract and to the version of the engine, and the founder has not asked for a number to be moved |
| How near is near | In the label of every measure that counts within 800 m, and in each step that counts | Not by the file. It is a change to the catalogue, in code: the labels say the distance |

## 7. Where it lives, and its routes

`tools/desk/panel/` holds what reads a release and what writes a change, `tools/desk/page/panel.*` the page, and `packages/pipeline/src/burro_pipeline/changes.py` the one reader of the file, which the desk uses too. The queues of the desk need no package, as before. The panel needs core, to work a band and a rank out as a build does: no second copy of that arithmetic is written.

`make desk` opens the panel. The address of the desk is its first screen, and the queues are one press away, at `/page/index.html`. Every route is under `/api/panel/`, is held to the rules of [the desk's server](desk.md), section 4, and carries `synthetic`.

| Route | Takes | Gives |
|---|---|---|
| `GET home` | | What is served, what waits for a person in each queue, how many things are flagged, and what was changed and not yet built |
| `GET moved` | | What differs between the release that is shown and one other, which is named as the desk starts: the areas, measures and vibes that came or went, how far the figures of each measure moved, how many areas changed band on each vibe, which files behind the two builds differ, and the first ten areas of the three searches, before and after. With no other release named, one line that says how to name one |
| `GET areas`, `GET outlines` | | Every area with its name, its borough, its label and a point inside it. The outline of every area, as the release draws it |
| `GET area/{id}` | The id of an area | Every figure with its unit, its sources, its date, the files it rests on and its state. What a home sells for. Every vibe with its band and its parts. What it has no figure for, and why. The flags that stand on it |
| `GET measures`, `GET measure/{id}` | The id of a measure | Its spread, the areas highest and lowest, the areas with no figure, and what stands out |
| `GET measure/{id}` | The id of a measure | Its spread, the areas highest and lowest, what stands out and the areas with no figure. Under `adjust`, its two labels as they stand for the reviewer, and whether they may be changed |
| `GET vibe/{id}` | The id of a vibe | Its recipe, the band of every area, the areas highest and lowest, how closely it follows homes per hectare and the distance from the middle of the areas, and the bands that rest on little. Under `adjust`, what a slider starts from: the shares as they stand for the reviewer, and the least and the most a part may hold |
| `GET flags`, `GET history` | | Every flag that stands, newest first. Every line of every reviewer, newest first, and where two reviewers differ |
| `POST flag` | `of`, `why`, `leave_out` | The line as written |
| `POST take-back` | `n`, `why` | The line as written. Only a line of the reviewer's own is taken back, and once |
| `GET numbers` | | The numbers set by judgement, each with what it is today, its unit, where it is and how it is changed |
| `GET brands` | | The table of tiers as it stands for the reviewer: every chain with its kind, its tier and each way the file of places writes it, and the chains that were taken out |
| `POST preview` | `what`, `of`, `now` | What the change would move, and `seen`, the mark of what was looked at. Nothing is written |
| `POST keep` | `what`, `of`, `now`, `why`, `seen` | The line as written. It is refused without the mark of the preview of that very change |

**What would move.** "Before" is the release as a build would make it today: core's own, with every change the reviewer has kept laid over it. "After" is that with the change that is proposed. So what is shown is what this one change moves. The panel says how many areas change band, how many go up and down, the ten areas that rise most and the ten that fall most, by the change in where each stands, and the first ten areas of three searches. An area is said by its band, and never by the score it is ranked on. A search is ranked by `rank()`, from the edits in `tools/desk/panel/searches.json`, and says what of it the release cannot hold. The founder's own sentence is read from the evaluation set, and its journey names its place by where the words stand in the sentence, so that no file of the panel holds the name.

**Sliders that always come to 100.** When one share is moved, the others share what is left in the proportion they stood in, in whole hundredths, and each holds from 1 to 59, or to 40 beside a part that counts who lived there. `rebalance()` in the page holds it. The desk holds what is sent to `checked_recipe()` whatever the page did.

**The table of brands.** A row of the table holds the name of a chain, its kind, its tier, and each way the file of places writes it. A row a change made is the founder's, and says so. A chain that is added is counted in its tier and in the mix. Core names no measure of it, so it cannot be asked for by name until core gains its id, which is a change to the catalogue. The panel says which measures a build works out again, and that what they move is known only once it is built. `brand_tiers.toml` is not written by the panel: it is what a build starts from.

**A name a person gave.** The name of a vibe and of each of its ends, what a vibe cannot see after the line every vibe says first, and the two labels of a measure. Each is held to the rule of a name in core, by the reader a build uses, before it is shown as looked at. A release that carries one is served by it wherever the API reads the release: the catalogue of `/v1/meta`, every fact and sentence of an area, and the rows of a comparison. **The words of an offer are not yet the release's.** What the reader offers of a sentence that is not plain, and the chip of an edit, say the name core gives: `wording.py` in the API and `interpret.py` in core read `TAGS` and `FEATURES`. And the reader knows a vibe by the words of core's lexicon, so a new name is shown and is not yet read. Until both read the release, a vibe that is renamed has two names on the website.

**What was built.** The lock of a release names the file of changes it was built with, by its hash and its length. A line is never changed and never removed, so that file is the start of the file as it stands. The first screen lists what stands now that did not stand then: what was changed since, and what was taken back since.

**What moved between two builds.** `make desk RELEASE=FOLDER BEFORE=FOLDER` holds the release that is shown against one other: the release that is served today, where the one that is shown is a build that waits to be approved. What differs is worked out once, as the desk starts, by the step `moved` of the pipeline: the screen draws what `python -m burro_pipeline moved BEFORE AFTER --out FOLDER` writes to `moved.json`, and no second copy of the comparison is written. An area is named, with its borough, where it came, went, bears another name or moved most. **Nothing on the screen is a press.** A build is approved by committing its lock ([ADR 0030](../adr/0030-a-release-is-kept-approved-by-its-lock-and-carried-in-the-image.md)), and the panel approves none. The sentence a search was read from is not shown on this screen, and is in nothing the step writes.

**A vibe that is a rough guide.** Village feel is served though it did not reach the bar, and says that it is less sure than the other vibes: decided by the founder on 2026-09-25 (ADR 0013, as amended). The panel says so beside the name of the vibe wherever it names one: where every vibe is listed, in the audit of an area, on the screen of the vibe over its sliders, and on the screen of what moved. It says core's label and core's sentence, as the website and the app are served them, and nothing is pressed to read either. Whether a vibe is a rough guide is core's, and no change at the panel moves it.

**What stands out.** A figure is far from the areas beside it where its percentile is 50 or more from the middle one of theirs, and three of them or more have a figure. A figure is at nought where those beside it are not where it is 0, every area beside it that has a figure is over 0, and two or more have one. A band rests on little where under 75 in 100 of its recipe has a figure in the area. Each number is a first guess.

## 8. What is built

| Step | Built | Held by |
|---|---|---|
| 1. This page | 2026-09-25 | |
| 2. The audit of an area, a measure and a vibe, with flags, the history and taking back | 2026-09-25 | `tools/desk/tests/test_panel_look.py`, `test_panel_server.py`, `test_panel_at_the_desk.py`, `tools/desk/page/test/panel.test.mjs`, `packages/pipeline/tests/test_changes.py` |
| The change to core of section 2, and a build that reads the file | 2026-09-25 | `packages/core/tests/test_adjusted.py`, `packages/pipeline/tests/assemble/test_preview_with_changes.py` |
| 3. The shares of a recipe, with what would move, kept as a line that a build reads | 2026-09-25 | `tools/desk/tests/test_panel_preview.py`, `test_panel_at_the_desk.py`, `tools/desk/page/test/panel.test.mjs` |
| 4. The table of brands: a chain is moved to another tier, added or taken out | 2026-09-25 | `tools/desk/tests/test_panel_brands.py`, `packages/pipeline/tests/derive/test_brands_with_changes.py`, `packages/pipeline/tests/assemble/test_preview_with_changes.py` |
| 5. The name of a vibe and of its ends, what it cannot see, and the label of a measure | 2026-09-25 | `tools/desk/tests/test_panel_relabel.py`, `services/api/tests/test_names_a_person_gave.py` |
| 6. The numbers set by judgement, listed. None is changed at the panel | 2026-09-25 | `tools/desk/tests/test_panel_numbers.py` |
| 7. The history, newest first, with taking back, and two reviewers shown to each other | 2026-09-25 | `tools/desk/tests/test_panel_server.py`, `test_panel_preview.py` |
| 8. What moved between the release that is shown and one other | 2026-09-25 | `tools/desk/tests/test_panel_moved.py`, `test_panel_at_the_desk.py`, `tools/desk/page/test/panel.test.mjs`, `packages/pipeline/tests/upkeep/test_moved.py` |
| 9. A vibe that is a rough guide says so beside its name | 2026-09-25 | `tools/desk/tests/test_panel_look.py`, `test_panel_moved.py`, `tools/desk/page/test/panel.test.mjs` |

No browser has opened the panel. Every screen was read by a test, as text, and nobody has seen how one looks.

## 9. A file of changes that was written by hand

The file is plain, so that it can be read with no panel. So it can be written with none, and **nothing the panel refuses protects what is served**. What protects it is what the reader of the file, the build and core refuse. The panel asks the same reader and the same rules before it keeps a line, so that nothing is kept that a build would stop at.

| Who refuses | When | What it can know |
|---|---|---|
| The reader, `burro_pipeline.changes.read` | Before anything else of a build, and before the panel keeps a line | One line at a time, and the lines before it |
| The build, `preview --changes` | Before the store is looked for, and again once the file of places is read | Core's catalogue, the table of tiers, the repository it runs from, and the publishers' files |
| Core, `parse_release` and `open_served` | When a build checks its release before it writes it, when `burro-release check` runs, and when the API loads a release | The release, and the lock beside it. Nothing else |

| A change that was written by hand | Refused by | The rule |
|---|---|---|
| A recipe gains a part, whatever the part | The reader, where the line says so. The build, where the line says the part was there. Core, in a release | `change_is_of_its_kind`, `change_was_made_of_what_stands`, `recipe_holds_cores_parts`. In core, `vibes_match_core` |
| The part is of a table of the census, or is household income | The same. Neither is a feature of core, so the reader refuses the line by its shape, and core the release | `change_is_of_its_kind`. In core, `catalogue_matches_core` |
| A part that counts residents is read from its low end, or put in a scale | No line can say which end a part is read from: a share is a whole number. Core refuses a release that says so | `change_is_of_its_kind`, `line_is_a_line`. In core, `vibes_match_core` |
| A part is given more than 40 in 100 where residents are counted | The build, and core | `recipe_keeps_its_rules`. In core, `vibes_match_core` |
| A vibe that is held off is placed by a change to its shares | Core, when the build checks its release. `tag_raw` places a vibe that is held off on no area without the part it is held off for, whatever its shares. No vibe is held off today: Village feel was, until the founder chose on 2026-09-25 to serve it as a rough guide (ADR 0013, as amended). The rule stands for any vibe that is held off in future | `held_off_stays_held_off`, `raw_matches_recipe` |
| The parts of a recipe that rest on the conservation areas are given 60 in 100 or more between them | The build, and core | `recipe_keeps_its_rules`. In core, `vibes_match_core` |
| A vibe is said to be a rough guide, or one that is said to be as sure as the rest | No line can say it: it is no part of a change. Core refuses a release that says of a vibe what core does not | `change_is_of_its_kind`. In core, `vibes_match_core` |
| A name holds a word for a group of people, praise or blame | The build, and core | `name_is_plain`. In core, `vibes_match_core` and `catalogue_matches_core` |
| A name holds a figure, or a label a figure that core's label does not say | The build, and core | `name_is_plain`, `says_what_it_cannot_see` |
| A name holds the name of a place | Core, when the build checks its release, by the names of the areas, the boroughs and the places of that release | `names_name_no_place` |
| A chain of the table has more than its tier changed | The build | `chain_moves_by_its_tier_alone` |
| A chain is added under a name the file of places does not write, or writes for fewer than two places that stand apart | The build, the second once the file of places is read | `chain_is_named_as_it_is_written`, `chain_is_seen_to_be_one` |
| A line names its reviewer by a name or an address, or writes a field twice | The reader | `reviewer_is_a_label`, `line_is_a_line` |
| The file is another reviewer's, or is not the copy the repository holds, or was changed since it was committed | The build | `changes_are_the_founders`, and a refusal in words. A change that is staged is refused by the lock: `tree_has_no_changes` |
| A release that carries a change is served with no lock, or with a lock that names another file or none | Core, in `open_served` | `real_release_has_its_build`, `changes_are_named`, `changes_are_locked`, `build_is_as_it_was_written` |

**What cannot be told, said plainly.**

- **The name of a place.** Core holds no list of the places of the world. A name a person gave is held to the names the release holds: its areas, their boroughs and its places. The name of a place the release does not hold is not found. A name of one word that is also a word, as a bank is, is refused where the release holds a place of that name, unless core's own labels say the word.
- **A chain.** A chain is told from a person and from one shop by the file of places, and by nothing else: its publisher gives a place a brand where it has matched the place to a chain. A name the file writes as the brand of two places or more that stand apart is that of a chain. A chain the file does not know is refused though it is one, and is added to the table in the repository, in a change that a person reads. **Core cannot refuse a chain**: the table of tiers is no part of a release, and core does not read the words of a definition.
- **The copy that was published.** Nothing marks a file as the one `desk publish` wrote. What a build takes is the file the repository holds, at the commit that is checked out, so a file that was written by hand is built only once it is committed, where it is read as any other change is. The lock names the commit.
- **A release that was written wholly by hand.** None of the manifest, the hashes and the lock is signed. Whoever can write all three, and a release that keeps every rule, has made a build of their own. What can tell it from another is the record of the builds that were approved, which is committed, and which nothing reads when a release is served.
