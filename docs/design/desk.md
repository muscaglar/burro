# The review desk

1. **Start it.** At the root of the repository type `make desk`. It fills the made-up city the first time, and prints `Open http://127.0.0.1:8765/`. Type that address into a browser on the same machine, or click it. If the browser then shows a short page that says the desk did not show itself, press "Open the desk" on it. `Ctrl-C` stops the desk.
2. **What you see.** The top line reads "MADE-UP CITY. Nothing here is a real place." Over the page is a list of the twelve queues, in the order of the work, each with how many items are left and what it waits on. Under the top line is the line that says what was saved. The name of the item stands over the item, the question and the answers are on the right, and the bottom line holds the keys.
3. **Do this first.** Press `3` for Kinds of venue, and answer ten items with `1`, `2` or `3`. Try `s` to skip, `u` to undo, `n` for a note and `?` for every key. Then press `q` and `8`, for Borders, to see a map: `.` and `,` page what is known of the area, and `m` takes up the cell under the cross.
4. **Nothing is lost.** Each answer is on disk before the next item is shown, under `data/raw/desk-synthetic/decisions/`, and under `decisions-private/` beside it for the queues that are never published. Close the page or stop the desk, start again, and it opens where you left off. On real data each line is also written to a second copy in a folder outside the repository, and real data is not served without one: section 3 says which folder, and how to make it.
5. **What it is for.** `make desk-compile` makes a build's files from the answers, and lists what you flagged. `make desk-publish` makes the copy of the decisions that may be committed. On the made-up city everything stays under `data/raw/desk-synthetic/`, where no build looks. When real files are in `data/raw/desk/`, the top line reads "REAL DATA FOR LONDON. A draft that nobody has checked. What you decide here is built."

**To sit down at the draft of London.** Ten lines, in the order of the work. Every path is in the repository, under `data/raw/`, which git ignores.

1. **Make the draft.** `BURRO_STORE_FOLDER=FOLDER uv run python -m burro_pipeline.areas.draft_run --out data/raw/areas-draft`, where FOLDER is the folder that holds the fetched files. It takes about two minutes, reaches no network and prints one line of counts.
2. **Take it to the desk.** `make desk-take DRAFT=data/raw/areas-draft`. It fills five queues in `data/raw/desk/`, and says how many items each holds, and how many names stand by a rule you have decided and are not asked about.
3. **Start the desk.** `make desk`. It keeps a second copy of every answer in the folder `burro-desk-decisions` in your home folder, and does not start until that folder is there: section 3 says how to make it, once. `make desk KEEP=FOLDER` keeps the copy in another folder of your own, outside the repository. It prints `Open http://127.0.0.1:8765/`.
4. **What you see.** The top line reads "REAL DATA FOR LONDON. A draft that nobody has checked. What you decide here is built." Under it is the list of queues, each on a key: Rules, Boroughs you know, Names, Borders, Whole boroughs.
5. **Do this first.** Press `1` for Rules, and read each of the eight: the rule, what it would settle, what you have decided already, what could go wrong, and the ten items drawn from it. `.` reads on, and `]` shows the next rule and decides nothing. `o` opens the first of the ten with its map, `]` and `[` go through them, and `o` comes back to the rule. `1` adopts a rule, `2` leaves each item to be read, and `u` takes either back.
6. **What you have decided is not asked again.** One official publisher is enough for a name, so the first three rules have nothing left to settle: each says so, and either answer takes it off the queue. The fifth rule leans on the fourth. It settles a name only where the fourth is adopted too, in whichever order you answer, and its screen says what a yes would settle as they stand.
7. **Then** press `q` and `2`, and say how well you know each borough. The boroughs you know well are offered first from then on.
8. **Then Names**, with `q` and `3`. The ring on the map is where a record puts the name, `.` reads on in what is known, `j` goes to the next flagged name, and `Enter` gives the answer the draft proposes.
9. **Not yet: Borders and Whole boroughs.** A name of an area that is turned down waits for a new draft. When every name is read: `make desk-compile ARGS="--data data/raw/desk"`, then the command of line 1 with `--out data/raw/areas-draft-2 --decided data/raw/desk/out/names.csv --ids data/raw/areas-draft/made/names/ids.csv`, then `make desk-take DRAFT=data/raw/areas-draft-2`.
10. **Then Borders**, with `make desk` again. Every answer is on the disk before the next item is shown, so stop with `Ctrl-C` and start again when you like.

Status: built, 2026-09-23, and mended on 2026-09-24 after two reviews and two sittings. Real files have been fetched since the desk was built, and a draft of London's areas was made from them: [the report of the first draft](../research/data/m3-first-draft.md) says what the desk's fill step and its server did with it. Nothing of that draft is in the repository. The page was first opened in a browser on 2026-09-24, on the made-up city, by a program that strikes keys and not by a person, in a tab that was out of view. What that sitting found was mended the same day. No mend of that sitting has been looked at again on the made-up city: section 10 lists what to look at again, in order, and what no sitting has yet seen. On 2026-09-24 the desk was given what the first draft of London asked of it: section 11. It has filled its queues from that draft and answered over its own port. The page was opened on that draft once, on 2026-09-24, by a program and not by a person: section 12 says what that sitting read, what it found and what was mended. What it left as wrong was closed the same day, with no browser open: section 13 says what was changed, and what to look at in a browser, in order. No person has sat at the draft of London. On 2026-09-24 the founder decided that one official publisher is enough for a name, and where the second copy of every decision is kept: section 14 says what the desk does with each, and what each queue then holds. Every count and hour is another design's estimate unless it says "guess", and none was timed. It rests on AGENTS.md rules 1, 3, 8, 9 and 13, ADRs 0004, 0006, 0010 and 0014, [the plan for London](london-data.md), [areas](london-data-areas.md), [researcher](london-data-researcher.md), [vibes](vibes.md) section 6 and [the first look at Overture](../research/data/overture-places.md).

The desk is where a person looks at data and decides. It runs on that person's own machine and opens in their browser: one small server, one page, plain files. It takes the place of the static review page of areas section 9, and answers part of row 16 of london-data section 14.

## 1. The queues

In the order of the work, which is the order the page lists them in. "Waits" is the milestone of london-data section 4 that needs the decisions. "After" is the queue a queue is made from: the page says how many items of that queue are left, in the list and while the queue is worked. `claims`, `whole` and `articles` were named by nobody and are added. Section 9 lists what was dropped.

| Queue | One item is | Shown | Items for London | Each | Hours | A decision changes | Waits | After |
|---|---|---|---|---|---|---|---|---|
| `rules` | A rule a draft puts to the founder | The rule in words, how many items it would settle, what could go wrong, the table of the draft that lists them all, and ten of those items drawn at random, each of which can be opened | 8 | 2 min, a guess | 0.3 | Whether the items the rule fits are settled with no person reading each | M3 | |
| `know` | A borough | Its outline among the others, and its name | 33 | 5 s | 0.1. The plan gives 1 | Which boroughs a reviewer is offered first, in `names`, `borders`, `whole` and `ratings` | M3 | |
| `kinds` | A record from a sample of one kind of venue | The name and the category as written, and who gave the record | 600, a guess: 12 kinds of 50 | 6 s, a guess | 1 | Whether the rule for a kind is kept, narrowed or dropped | M2 | |
| `commons` | A named common, heath or forest | The name, and the nearest matches in the greenspace file | 20 | 1 min | 0.3 | Whether Parks close by ships or waits | M2 | |
| `figures` | A figure the coverage report flagged | The figure, its unit, source and vintage, and the same figure in each neighbour | Not known before the first report | 15 s, a guess | Part of tasks 12 and 22 | A list the founder reads before approving a release. It changes no figure | M2, M7 | |
| `sentences` | A sentence of an article of the golden set | The sentence, the one each side, its heading | 30 articles. Sentences not counted | 12 min an article | 6 | The golden set, which gates the first research run | M2 | |
| `names` | A candidate name | The name as each publisher writes it, where each record puts it, the tier the score proposes, and every doubt the draft has of it | 1,100 | 45 s | 14 | `areas.csv`, `aliases.csv`, `name_evidence.csv` | M3 | `rules` |
| `borders` | A flagged area. On the better route, every area | Its cells over the layers of section 6, why it was flagged, the evidence rows of its border cells | 120, then 450 | 8 min | 16, then 60 | Rows of `oa_to_area.csv`, and the area's `review_state` | M3, M7 | `rules`, `names` |
| `whole` | A borough | Every area of the borough at once | 33 | 15 min | 8 | As `borders` | M3 | `rules`, `names` |
| `ratings` | An area on one vibe | The outline over the layers of section 6, and the rubric. No score and no band | 120 a rater, for 25 to 30 raters | 10 s, a guess | 0.3 a rater | The people test of vibes 6.2, which says which vibes ship | M6 | `names` |
| `articles` | A row of the map of areas to articles | The area, the title of the article, whose article the map says it is, and its ids. No word of the article | 860 | 20 s | 5 | Which pages the research run fetches: researcher section 4, step 1 | M8 | `names` |
| `claims` | A quotation | The words, the sentence each side, the kind, which checks flagged it, the address of the revision as text | 3,100 | 25 s | 21 | The claim's `review`. Only an accepted claim enters `claims.json` | M8 | `articles` |

**The order of the work.** Rules, then names, then the draft made again, then borders. The desk cannot take the ground from under an area: only the areas build gives an output area to an area. So an answer that turns the name of an area into another name, or drops it, is saved, and `compile` sets it aside while the area has cells. The areas build reads such answers from `out/names.csv` and makes the draft again without those areas. The queues are filled again, and only then are `borders` and `whole` looked at. The page says this before such an answer is given, and `borders` and `whole` say so while one waits: section 5. A name decided after its border was looked at opens the border again, which is why the page says what a queue waits on.

**The order inside a queue.** A queue that is read a part at a time puts its flagged items first within the part, so that a part is finished. `names` and `borders` are read borough by borough, and a borough is finished before the next begins. The borough with most at stake comes first, as the draft says in `order.csv`, and a borough the draft does not place comes after, by name. In a borough of `names`: the names proposed as areas, then the other names, and in both the flagged first and then the most at stake. In a borough of `borders`: the flagged first, then the most at stake. `whole`: the flagged boroughs first, then the most at stake. `claims`: area by area, because an area ships as soon as its own claims are read. `articles`: area by area, the area's own article first. `kinds`: kind by kind. `rules`: as the draft puts them, because a rule settles only what no rule before it settles. Every other queue puts its flagged items first. In `names`, `borders`, `whole` and `ratings` the boroughs a reviewer marked in `know` as known well are offered first, then those known a little, then those not marked, and those not known last.

**Who works a queue.** The founder works every queue. A reviewer who is not `r1` is listed `know`, `borders`, `ratings` and `claims` and no other, so that a rater does not meet figures of crime or of prices on the way to a rating. Only the founder adopts a rule.

## 2. One shape for every queue

A queue is a list of items and one question. The page shows one item, and one key decides it. The same everywhere: the item, the question, up to nine answers on the digits, a note, skip, undo, a mark that asks for a second reviewer, the progress, and the line written. A queue may add seven things and no more: a view, `map` or `text`; one control, `pick` or `move`; words from the item in its question, as `{kind}`; one line of rule under the question; other words for the question once a cell is moved; one answer that is given to every item of a part; words for an answer that a build will set aside. The view `text` shows the item's `text`, or its `lines` when it has none.

| Queue | Question, version 1 | Answers, in key order, by code | View, adds | Its lines | An `item`, and the `detail` of its line |
|---|---|---|---|---|---|
| `rules` | Shall this rule settle what it fits, with no person reading each? | `yes`, `no` | text | Public | `a_ward_of_its_name`. `{"rule":"a_ward_of_its_name","queue":"names","gives":"proposed","settles":"9f2c41d07ab3"}` |
| `know` | How well do you know this borough? | `well`, `a_little`, `not` | map | Private | `quillhaven`. `{}` |
| `kinds` | Is this a `{kind}`? | `yes`, `no`, `cannot_tell` | text | Public | `syn-p0037`. `{"kind":"landmark","source_id":"synthetic"}` |
| `commons` | Is this place in the file, with a name and a way in? | `in_file`, `no_name_or_way_in`, `not_in_file` | text | Public | `c:thrushcombe-green`. `{"record_id":"syn-p0043"}` |
| `figures` | Does this figure look wrong for this area? | `looks_right`, `looks_wrong`, `cannot_say` | text | Public | `syn-n0004:air_no2`. `{"area_id":"syn-n0004","feature_id":"air_no2"}` |
| `sentences` | Is this sentence fit to quote about the place? | `fit`, `residents`, `safety`, `praise`, `person`, `change_or_price`, `not_a_place` | text | Private | `syn-page-3:17`. `{"page_id":3,"revision_id":1,"sentence":17}` |
| `names` | Is this the name of an area? | `area`, `same_ground`, `inside`, `wide`, `drop` | map, `pick` | Public | `n:syn-n0004` for a name proposed as an area, `a:syn-n0004:dulcimer` for an alias. `{"of":["syn-n0004"],"pick":"Dulcimer","proposed":"inside"}`. An area with ground adds `"holds":"cells"`, and an item a rule fits adds `"fits"` and the rule, and `"leans_on"` and the rule it leans on where the rule that fits leans on others |
| `borders` | Is this boundary right? After a move: With your moves, is it right now? | `right`, `wrong`, `unknown` | map, `move` | Public | `syn-n0007`. `{}`, or `{"fits":"a_few_cells_across_a_borough_line"}` |
| `whole` | Is anything wrong in this borough? After a move: With your moves, is anything still wrong in this borough? | `right`, `wrong`, `unknown` | map, `move` | Public | `quillhaven`. `{}` |
| `ratings` | `{rubric}` | `1`, `2`, `3`, `4`, `5`, `cannot_say`, and on key 7 `cannot_say` for every vibe of the area | map | Private | `syn-n0004:leafy`. `{"area_id":"syn-n0004","vibe":"leafy"}` |
| `articles` | Is this the article about this place? | `its_article`, `not_its_article`, `cannot_tell` | text | Public | `syn-n0004:syn-q0004`. `{"area_id":"syn-n0004","qid":"syn-q0004","page_id":"6004","role":"own","proposed":"its_article"}` |
| `claims` | May this be shown as the source's words about this area? | `accept`, `not_this_place`, `describes_people`, `passes_judgement`, `not_fair` | text | Private | `syn-c0a1b2c3d4e5`. `{}` |

- The rule under `names`, `borders` and `whole`, from areas section 9 and row 13 of london-data section 14: "Use what you know and what the page shows. Copy no name and no border from a map or a website. Move a border for the ground, never for who lives there. If you rely on a document, give its address in the note."
- A move is a line of its own, written when it is made: the same `item`, the cell as `part`, the answer `move`, and `{"from":"syn-n0007","to":"syn-n0012"}`. `wrong` needs a note, and so does an answer given after a move: the page opens the note and waits.
- **After a move the question changes.** "Is this boundary right?" reads, after a move, as "was the draft right?". Both answers apply the move, and only `right` says that the border is checked. So once an item holds a move the page asks "With your moves, is it right now?", with the answers "Right now" and "Still wrong". An area called wrong is listed for the founder, with its note: section 3.
- **The answer the draft proposes** is in the item's `preset`, as `proposed`. The page marks it among the answers, and `Enter` gives it, whichever digit it is on. A name proposed as another name of an area cannot be made an area at the desk: only the areas build gives an area its id. So the page does not offer that answer on such a name: every other answer keeps its key, and a line over the answers says why there is no key `1`, and to write a note and skip. The desk refuses the answer from whatever sends it.
- **An answer that does not know** is `unknown`, `cannot_say` or `cannot_tell`. It decides nothing: section 3.
- **An answer that a build will set aside.** The item of a name proposed as an area says what the area holds, in its `preset`: `holds` is `cells` where cells are drafted to it, and `names` where it has no cell and another name is given to it. The question of `names` says under `set_aside` which answers turn a name down, and gives the page its words. The page says them before the answer is given: section 5.
- **A rule is adopted by the founder, and by nobody else.** A draft puts rules in `rules.csv`, and in `rules_items.csv` the items each would settle. The desk adopts none by itself. `yes` writes a line for every item the rule fits that the founder has not answered, in the founder's own file of that item's queue, with the rule named in its `detail`. `no` writes nothing but itself. When a `yes` no longer stands, because it was undone, changed to `no`, or given to another list of items than the draft now puts, every line it wrote is taken back by a line of its own. The founder's own answer to an item is never written over, and may be given to an item a rule settled.
- **A rule that leans on others settles only what they, once adopted, would settle.** A rule may let an item through to the rule its records fit, and have no test of its own: the fifth rule of the first draft of London says that a mark asks nothing. The draft names the rules such a rule leans on, and for each of its items the one that item leans on. The desk settles the item only where both are adopted, in whichever order. While the rule leant on is not adopted the item is left open, and the answer to the rule says how many items that holds back. When the rule leant on is no longer adopted, what was settled by leaning on it is taken back with it. A rule leans only on a rule of its own queue that is put before it and leans on none.
- **What a rule gives an item** is in the rule's `preset`, as `gives`: `proposed` for the answer the draft proposes for the item, an answer of the item's queue, or nothing. A rule gives a border nothing: it leaves the border as drafted, and the line's answer is `rule`, which is no answer of any question and says nothing of whether the border is right.
- "Public" means the lines may be published, by `desk publish`. A private line says where a person knows, or judges words about a real area: it is kept in a tree of its own, and only counts made from it are published.

## 3. The records

A decision is one line of JSON, appended to `<data>/decisions/<queue>/<reviewer>.jsonl`, or to `<data>/decisions-private/<queue>/<reviewer>.jsonl` where the question says `public: false`. Nothing is ever changed or removed. Lines found in the wrong tree stop the desk and the build, and are named.

| Field | Type | Holds | Published |
|---|---|---|---|
| `n`, `at` | int, str | The line's number in its file, from 1. The server's clock, UTC, to the second | `n`. `at` cut to the day |
| `reviewer` | str | `r1` to `r99`. A label, never a name. `r1` is the founder and `r2` the second reviewer | Yes |
| `queue`, `question` | str, str | The queue, and the version of the question asked: `names@1` | Yes |
| `item`, `rev`, `part` | str, str, str | The item's id. 12 hex digits of the hash of what was shown. `part` is empty for the item's answer, and the code of a cell for a move | Yes |
| `answer` | str | A code of section 2, or `skip`, `move`, `undo`. `rule` where a rule the founder adopted leaves the item as drafted | Yes. No `skip` and no `undo` is published |
| `note`, `second` | str, bool | Up to 500 characters, one line of plain text: no control character, no mark that is not seen, no end of line. True asks for a second reviewer | Yes |
| `settles`, `undoes` | bool, int or null | True ends a dispute, from `r1` alone. The `n` of the line an `undo` takes back | `settles` |
| `detail` | object | What the item was made with, its `preset`, and nothing a caller made up. A queue that adds `pick` may change `pick` and `of`. A move holds `from` and `to`. A line that a rule wrote holds `rule`, which only the desk can write | Yes |
| `seconds`, `synthetic` | int, bool | How long the item was on screen with the tab in view, 900 at most. True when the item was of the made-up city | `synthetic` |

```
{"n":412,"at":"2026-10-06T21:14:09Z","reviewer":"r1","queue":"names","question":"names@1","item":"n:syn-n0004","rev":"9f2c41d07ab3","part":"","answer":"area","note":"","second":false,"settles":false,"undoes":null,"detail":{"of":[],"pick":"Dulcimer Green"},"seconds":31,"synthetic":true}
```

As published, the same line says the day and never the hour, and leaves out the time on screen:

```
{"n":412,"at":"2026-10-06","reviewer":"r1","queue":"names","question":"names@1","item":"n:lon-n0004","rev":"9f2c41d07ab3","part":"","answer":"area","note":"","second":false,"settles":false,"detail":{"of":[],"pick":"A name"},"synthetic":false}
```

**Which line stands.** For one reviewer, item and part: the last line that no later line undoes. A `skip` stands as not decided. A line whose `rev` is not the item's `rev` today, or whose `question` is not the question today, is stale: it is kept, it is not applied, and the item is open again with the old answer shown. The `rev` of a border, a whole borough and a rating is made from the cells and what placed them, and from no name: a name respelt reopens no answer about the ground.

**A line that a rule wrote.** It is in the founder's file of the item's queue, with the answer the rule gives, the rule in `detail.rule`, no note and no seconds. It stands as any line stands, and the item is done: it leaves the queue. It is counted apart, as `by_rule`, and is left out of the pace. `u` in a queue never takes such a line back: it is taken back with its rule, in `rules`. A line whose answer is `rule` decides nothing between reviewers, as a skip decides nothing: what a reviewer says of the border stands.

**A rule that is asked again.** A yes is given to one list of items. When the queues are filled from a draft that gives the rule another list, the yes is stale, and the rule is open again with the old answer shown. Until the founder answers it, what it settled stands where the item has not changed, and nothing more is settled by it. A `no`, or an undo, then takes back every line the rule wrote, those of items that are gone among them.

**A name that was turned down, once the draft is made again.** The draft leaves it out, so the desk is handed no item of it. Its line stands in the file all the same, and `out/names.csv` keeps its row, with `asked_today` as `false`. So a draft made from that table leaves the name out again, however often the draft is made.

**Two reviewers.** Each writes a file of their own, so a second reviewer works on another machine and sends one file back. An item that `r1` marked `second` comes first for `r2`. Where the answers that stand are the same, the item is agreed. Where they differ it is disputed: nothing is applied and the draft stands, as areas section 8 says, until `r1` writes a line that `settles`. An answer that does not know is left out where another reviewer decided: the founder meets ground they do not know, says so, and the reviewer's answer stands alone, with their moves in their name. So an area is never said to be checked by a person who said they could not check it. The page shows another reviewer's answer, and the cells they moved, only once your own stands, so that agreement can be measured.

**What a build reads.** `compile` is a pure function of the draft folder and the lines. It reads no clock and no network, and the same lines give the same bytes. It refuses to mix a synthetic line with a real one. A cell of a CSV that begins `=`, `+`, `-` or `@` gains a leading apostrophe. When a check fails it writes nothing, and says which. `decided_by` and `chosen_by` are `founder` for `r1` and `reviewer-2` for `r2`, a claim's `reviewer` is `founder` or `second`, and `decided_on` is the day of `at`. It removes from `out/`, and from the gazetteer of the made-up city, what the run did not make. It removes nothing from the gazetteer of London.

| Queue | Writes | Rule |
|---|---|---|
| `rules` | `out/rules.csv` | The founder's answer to each rule. What a rule settled is written in the table of the item's queue |
| `names` | `areas.csv`, `aliases.csv`, `name_evidence.csv` of areas section 5, in `--gazetteer`. `out/names.csv` | From `r1` alone. `area`: the row is in `areas.csv`, `review_state` becomes `name_checked`, and its evidence rows take `chosen_by` and `chosen_on`. `same_ground`, `inside`, `wide`: the row is in `aliases.csv` with that `kind`, once for each area in `detail.of`, five at most. `drop`: no row. `pick` sets the name, and only to a form a source wrote. An answer a rule gave is applied as the founder's, who adopted the rule, and `out/names.csv` names the rule in the column `rule`. An answer that turns down an area with cells is set aside, and `compile` says how many wait and from which file the draft is made again. A name that stands by a rule the founder has decided already is no item, and no answer is given to it: its row of `areas.csv` says `named_by_rule` as the draft wrote it, and no person is written as having chosen it |
| `borders`, `whole` | `oa_to_area.csv`, `areas.csv`, `not_applied.csv`. `out/borders.csv`, `out/whole.csv` | A move that stands sets `area_id`, `basis = reviewed`, `decided_by`, `decided_on`, and `reason` from the note of the answer on its item. A move with no such note, or in dispute, goes to `not_applied.csv`. `right` from one reviewer gives `boundary_checked`, from two `checked_twice`. `wrong` applies the moves and checks nothing. A border that a rule left as drafted is checked by nobody: its row of `out/borders.csv` holds the answer `rule` and names the rule, and its state is raised only by what a reviewer says. A state never falls. Checked before writing: every cell has one row, and every row names an area of `areas.csv` |
| `claims`, `sentences` | `out/private/claims_review.jsonl`, `out/private/golden.jsonl` | `claim_id` and the `review` of researcher section 5: `accept` is `accepted`, and any other code is `rejected` with that reason. `page_id`, `revision_id`, `sentence`, `fit`, `code` |
| `ratings`, `know` | `out/private/ratings.csv`, `out/private/know.csv` | The answers that stand, a row each, with the reviewer and what the item was made with |
| `figures`, `kinds`, `commons`, `articles` | `out/figures_to_check.csv`, `out/kinds.csv`, `out/kinds_counts.csv`, `out/commons.csv`, `out/articles.csv` | The same. `kinds_counts.csv` counts by kind: `asked`, `yes`, `no`, `cannot_tell`. `commons` passes when all 20 are `in_file` |
| Every queue | `out/private/to_look_at.csv` | What a person flagged: every answer that calls an item wrong, that does not know, that is marked for a second reviewer, or that is a skip with a note or a mark. `queue`, `item`, `title`, `reviewer`, `answer`, `why`, `note`. A rating that cannot be given is not listed: a rater is asked to say so |

Every row of every file under `out/` holds `note`, `second` and `synthetic`. What is made from private lines is written to `out/private/`, which only its owner may read. `compile` ends by saying how many answers were called wrong, were not known, were marked and were skipped with a note, and counts them apart from what was applied. It says how many items a rule settled, by queue.

**What may be committed.** `desk publish --to FOLDER` writes `<FOLDER>/decisions/<queue>/<reviewer>.jsonl`. It takes only the queues whose question says `public: true`, and only the lines that stand today: no line that was taken back, no skip, no line of an item that has changed. It refuses the made-up city. It prints every note once, for a person to read before they commit. It is as pure as `compile`.

**The kept copy.** The lines are under `data/raw/`, which git ignores, so `git clean -x` would take them. So each line is written to the same place under a second folder too, and is on the disk there before the desk answers. The folder may not lie in the repository or in the desk's own folders. When the desk starts it compares the two in full: it brings the copy up where it is behind, and where the copy holds what the folder has lost, or the two differ, it does not start, names the files and changes nothing.

| | |
|---|---|
| Where the copy is kept | In `~/burro-desk-decisions`: the folder `burro-desk-decisions` in the home folder of whoever starts the desk. The founder decided it on 2026-09-24 |
| How the folder is made | Once, by hand: `mkdir ~/burro-desk-decisions`. Let a backup take it |
| What the desk does where the folder is not there | It does not serve real data, and says which folder to make. It makes no folder by itself: one it made could be taken for the copy of an earlier sitting, and would hold nothing of it |
| How another folder is named | `make desk KEEP=FOLDER`, or `--keep FOLDER`. A folder that is named is used whatever the home folder holds |
| What the code holds | The name of the folder, and no path. It asks the machine it runs on where the home folder is |
| The made-up city | It keeps no copy unless a folder is named |

## 4. The server

Python's standard library and nothing else. It binds to `127.0.0.1` and to no other address. It writes only under `<data>/decisions/` and `<data>/decisions-private/`, and under the kept copy where one is named, and only by appending a line, flushed and synced before it answers. It never builds a path from the words of a request: a queue, an item, a group and a layer are keys of tables made at start.

| Route | Takes | Gives |
|---|---|---|
| `GET /`, `GET /page/{name}` | A name from the list of files in `page/`, made at start | The page. A `.mjs` file is served as `text/javascript` |
| `GET /favicon.ico` | | A drawing with nothing in it, so that the browser logs no fault for the lack of an icon |
| `GET /api/state` | | `desk` (1), `reviewer`, `token`, `banner`, `resume` as `{queue, item}` or null, `broken_lines` as the count of lines on disk that do not parse, `mended_lines` as the count of half lines that were written again whole, and `queues`, in the order of the work: `queue`, `title`, `total`, `done`, `wrong`, `not_known`, `skipped`, `stale`, `disputed`, `by_rule`, `flagged`, `flagged_left`, `second`, `median_seconds`, `last_hour`, `set_aside` as the count of the reviewer's own answers that a build will set aside, and `waits` as `{queue, title, left}` for each queue it is made from that the founder has not finished. A row of `waits` holds `set_aside` too where an answer in that queue waits for a new draft, whoever gave it, and is then listed though nothing is left |
| `GET /api/queue/{queue}` | | `question`, as `questions.json` holds it. `items`, in the order they are offered: `id`, `group`, `state`, one of `open`, `done`, `skipped`, `stale`, `disputed`, `flagged`, and `part` where one answer may be given to a whole part |
| `GET /api/item/{queue}/{item}` | | `item`, as section 8 gives it. `state`. `mine`: the line that stands, or null. `moves`: the moves that stand. `others`: `reviewer`, `answer`, `note`, `at`, `moves` as `{part, from, to}`, empty until `mine` stands. In `rules`, `leans`: for each rule the rule leans on, `rule`, `stands` as `adopted`, `asked_again` or `not_adopted`, and `items` as how many of the rule's items lean on it. Empty for a rule that stands by itself |
| `GET /api/layer/{group}/{layer}` | | The layer's file, as section 8 gives it |
| `POST /api/decide` | `queue`, `item`, `rev`, `part`, `answer`, `note`, `second`, `settles`, `detail`, `seconds`, `stands` | `line` as written, `next` as an item id or null, and the queue's counts. In `rules`, `ruled` as `{settled, taken_back}`: how many items the answer settled, and how many answers of a rule it took back. It holds `held_back` too where an adopted rule fits items that it does not settle, because the rule each leans on is not adopted |
| `POST /api/undo` | `queue` | `undone`, the line taken back, and the counts. Asked again, it takes back the one before. In `rules`, `ruled` too |

- Every answer under `/api/` is JSON and carries `synthetic`, errors included. An error is `{error, message, synthetic}`: `error` is one of `forbidden`, `not_found`, `bad_request`, `stale_item`, `already_answered`, `too_large`, `not_saved`, and `message` is fixed text.
- **Refused with 403:** a `Host` that is not `127.0.0.1:<port>` or `localhost:<port>`. An `Origin` that is not the server's own. A request the browser marks as from another site. A `POST` without `Content-Type: application/json`, or without the `X-Desk-Token` that `/api/state` gave. The token is made at start. No answer carries a header that lets another origin read it.
- **The address opened from another page.** A browser marks a click in a chat, in a terminal on the web or in any other page as from another site. Such a request for `/`, made to open a page and for nothing else, is refused with 403 like the rest, and its answer is a small page of fixed words in place of JSON: which data the desk holds, a link to `/`, and that the address can be typed. The link is a request of the desk's own page, which the desk takes. The small page holds no script, no token and nothing of the request. A page in a frame, a script, a fetch and every route under `/api/` and `/page/` get the JSON.
- **Refused as a bad request:** a body over 16 KB, a field it does not know, an answer that is not one of the question's, the answer `rule`, a `detail` that the item does not give, so a `detail` that names a rule, a note that is not one line of plain text, `area` on a name proposed as another name. A `rev` that is not the item's is `stale_item`, and the page shows the item again.
- **An answer from an old page replaces nothing.** `stands` is the `n` of the line the page showed as standing, or null. Where another line stands the desk refuses with `already_answered`, and the page reads the item again, shows the answer that stands, and says that the same key will change it. So a second tab costs one more key only when an answer is truly changed. The same answer given twice is written once.
- **A fault of the disk** is `not_saved`, with words by the number of the fault, which hold no path and no line: the disk is full, or the desk may not write to its folder, or the kept copy differs. The console holds the number. For any other fault the words say to start the desk again.
- **Every answer carries** `Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` and `Cache-Control: no-store`. So the browser itself refuses a request to any other host.
- **What is held between requests.** The desk holds what each file of decisions held when it was last read, with its size, its time of change and its place on the disk, and reads a file again only when one of them differs. So a second desk on the folder and a file sent back by another reviewer are seen at the next request. Nothing is kept from one run to the next. Timed through the desk's own port, with each line synced: an answer takes 21 ms at 3,000 lines, and 58 ms at 10,000. A `yes` to a rule writes a line for each item it settles, one after another, and answers when the last is on the disk: the rule that settles most of the first draft of London, 127 names, took half a second with a kept copy.
- **The desk trusts every program on the machine it runs on.** `GET /api/state` gives the token to any request that names the right host and sends no `Origin`. A page of another site cannot make such a request and read the answer, so the web is kept out. But the loopback address is shared by every account on the machine: another account cannot open the folder of decisions, which is the owner's alone, and can still ask the server for every item and write lines as the reviewer. On a machine with one account this changes nothing. It is accepted, for one person at their own machine.
- The reviewer is named when the server starts, never in a request. The server prints the address to open and opens nothing. After that it prints the method, the route's template and the status, and never an item, an answer or a note. It is tested through its own port, under `pytest.mark.allow_hosts(["127.0.0.1"])`.

## 5. The page

One screen, with no scrolling of the page. The item fills the left, under its name. A column of 22rem on the right holds what is known, the question and the answers. It is laid out for a window of 1280 by 720 and up, which leaves the page about 633 pixels of height, follows the system's light or dark, moves nothing by animation, and sets text at 16px or more.

```
+------------------------------------------------------------------------------------------+
| MADE-UP CITY. Nothing here is a real place.  Borders: 96 done, 14 not known, 10 wrong,   |
|                                              0 left, 7 min each                          |
+------------------------------------------------------------------------------------------+
| Saved: Right, for Tallowgate. Next: Foxholt.                 Waits on 4 in Names. A name |
|                                                     decided later opens its border again. |
+--------------------------------------------------------+---------------------------------+
| Dulcimer Green, Quillhaven                             | Here because: one publisher     |
+--------------------------------------------------------+  a  Dulcimer Green               |
| the map, or the text                                   |  b  Dulcimer                    |
|                                                        | As written      Dulcimer Green  |
| map: cells in the colour of their area, ward lines,    | More below. Press . to read on  |
| town centres, roads and their names, seed points       +---------------------------------+
|                                                        | Is this the name of an area?    |
| text: the sentence before in grey, the sentence,       | > The rule                      |
| the sentence after in grey                             | > This area has ground. To turn |
|                                                        |   its name down waits for a new |
| a rule: its lines, in the middle of the page           |   draft.                        |
|                                                        |  1  An area (proposed: Enter)   |
|                                                        |  2  Another name, same ground   |
|                                                        |     (waits)                     |
|                                                        |  5  Not a name to keep (waits)  |
|                                                        | Note  [                       ] |
|                                                        | [ ] Ask a second reviewer       |
+--------------------------------------------------------+---------------------------------+
| 1-9 answer  s skip  u undo  n note  f second  [ before  ] after  j flagged  g  q  p  ?   |
+------------------------------------------------------------------------------------------+
```

- **What was saved has a line of its own**, under the top line and across the page, so that it is never below a fold. It is two lines high whatever it holds, so that the map and the answers stay where they are from one item to the next. What went wrong is said there too, in a box of its own colour, and what the queue waits on is at its right.
- **The name of the item is printed once**, over the item. As an item appears its name is said aloud for a screen reader, and is not printed a second time.
- **What is known of the item** is in this order: why it is here, the spellings to choose from, the areas named, a dispute, your own answer, other reviewers' answers, the cells you moved, and then the rows of evidence, which are the longest. It scrolls, by the wheel and by `.` and `,`, and the page says "More below" while there is more below what is shown. The words go when the last line is in view, and come back when a person reads back. Each item is read from its top. Where it is long it keeps a floor of 8rem and the question gives way. Where it is short it takes nothing from the answers.
- **An answer that will be set aside is said before it is given.** The desk cannot take the ground from under an area, so an answer that turns the name of an area down is saved, and set aside when a build's files are made. On such an item a line over the answers says in short that the answer waits for a new draft, and each answer that waits is marked "(waits)". Under it is what to do: read every name first, then make the draft again from the answers, then look at borders. That is open on the first such item of a sitting, and shut from the next, as the rule is. What was saved says that the answer is set aside, the top line counts such answers apart from those done, and `borders` and `whole` say how many names wait for a new draft, and to make the draft again first.
- **A rule is read in the middle of the page**, as a record: the rule in words, how many items it would settle and how long those would take, what could go wrong, how many of them wait for a new draft, what the draft says of the rule, and ten of the items, drawn by a fixed shuffle. `.` and `,` page it. The draft says where every item the rule would settle is listed: for London, the file `rules_would_settle.csv` in the folder the draft was written to.
- **An item that is drawn is opened from its rule.** Before the ten the page says which key opens them. `o` opens the first in its own queue, as it is shown there: with its map, what is known of it and the answers. `]` and `[` go through the ten, and no further. `o` comes back to the rule. While one is looked at the line under the top line says which of the ten it is, and nothing is decided: a key that would answer, skip, undo or move a cell says so and does nothing. A queue chosen from the list ends the look. What was saved says how many items the rule settled, or that nothing was changed. A rule that leans on others says under "Leans on" how many of its items lean on each, and under "As the rules stand" which of them are adopted and what a yes would settle today: nothing, where none is. What was saved then says how many items wait until the rule each leans on is adopted. An item a rule settled says which rule, and that the person's own answer takes its place. An item a rule fits says so before any rule is adopted. The top line counts what a rule settled apart from what a person read.
- **A label begins the line of its value**, and the value has the width of the column. A label may be as long as a publisher and the name of its file. In a column of its own such a label left the value a few letters to the line.
- **The rule** is open on the first item of a queue in a sitting, and shut from the next. It is shut too where the line that says there is more to read takes the room of an answer. It is shut at once where it would push an answer out of view, as it does in Ratings in a window of 1280 by 720. A person who opens it keeps it open until the next item.
- **The words under the note**, "A note may be published. Write nothing about yourself or anyone else.", are shown while a note is written or kept, and at no other time.

| Key | Does, in every queue |
|---|---|
| `1` to `9` | Gives the answer in that place, writes it, and shows the next open item. In `ratings`, `7` says that the area is not known: it gives `cannot_say` to every vibe of the area that is still open, a line for each |
| `Enter` | Gives the answer marked as proposed, where one is |
| `s`, `u` | Skips: the item comes back after the rest. Takes back what the last key wrote in this queue, and shows its item again with its note and its mark. Where the last key of the sitting wrote several lines, as `7` in `ratings` does, one `u` takes them all back |
| `n`, `f` | Opens the note, which goes with the next answer: `Enter` keeps it, `Esc` leaves it, and no other key acts while it is open. Marks the next answer, or skip, for a second reviewer |
| `[`, `]` | Looks at the item before or after, and decides nothing. A note that was kept and a mark stay. Where no map is shown, Left and Right do the same |
| `j` | Goes to the next flagged item that is not done, past those that are not flagged, and decides nothing. It goes round to the start, and says so when none is left |
| `o` | In `rules`, opens the first of the items a rule shows. While one is open, `[` and `]` go through them and `o` comes back to the rule |
| `g`, `q`, `p`, `?` | Chooses a group, such as a borough. Lists the queues, each on a key of the top row. Pauses, which stops the clock. Shows the keys |
| `.`, `,`, Page Down, Page Up | Reads on in what is known of the item, and goes back. It decides nothing. An item that is read in the middle of the page, as a rule is, is paged there |
| `+`, `-`, `0`, drag, wheel, an arrow | Zoom in, zoom out, fit the item, move the map, move it by the keyboard an eighth of its shorter side. With Shift an arrow moves it a quarter as far, so that the cross can be put on any cell |
| `a` to `e`, a click, where a queue adds `pick` | Chooses a spelling. A click on a cell names an area the name is given to, five at most, and writes nothing. `same_ground`, `inside` and `wide` wait until one is named |
| Click, click, `Esc`, `m`, where a queue adds `move` | Takes up a cell. Puts it in the area of the cell clicked next, and writes the move at once. Lets go. `m` does what a click does, to the cell under the cross in the middle of the map |
| `Esc` | Lets go of a cell, leaves a note, closes a list, or drops a note that was kept and a mark |

- The top line always says which data is shown. For real files it reads "REAL DATA FOR LONDON. A draft that nobody has checked. What you decide here is built." What the desk is handed of London is what a method made, so the top line says so on every screen, and so does every list. It counts apart what was called wrong and what was not known, so that it never says work is done that a build will never see. In `ratings` it counts areas.
- It opens at `resume`: the first open item of the queue last worked in. Pace is the median `seconds` of the last 50 lines, and what is left is that times the open items. A page opened in a tab that is out of view counts nothing until it is seen.
- It moves on only when the server has answered. If the write fails it stays, says what the desk said, keeps the answer, sends it again until the server takes it, and asks before the page is closed. A key struck within a quarter of a second of a new item is dropped, and so is an undo.
- **It says what was saved**, and what went with it. "Saved: Right, for Tallowgate. Next: Foxholt." "Saved: Wrong, with a note, second reviewer asked, for Tallowgate." "Saved: 4, on leafy, for Cindermoor." "Saved: I do not know this area, 7 answers, for Cindermoor." "Taken back: I do not know this area, 7 answers, for Cindermoor." So a slip of the finger is seen, and so is a mark that was not meant.
- **One undo takes back what one key did.** The page holds the number of each line that each key of the sitting wrote. Where the last key wrote several, `u` asks the desk to take back one after another until all are taken back, and shows nothing in between. It stops at a line the page did not write, and at an undo the desk did not answer. After the page is loaded again it holds no such numbers, and `u` takes back one line at a time.
- **Words typed with the note shut are taken as no key.** Every letter is a key, so a note typed without `n` once took back an answer and skipped two items. A letter is now held a third of a second before it acts. Three letters inside a second are words, and so is a space struck while a letter is held: none of them is taken, the page says to press `n`, and what is struck in the next second is taken for one of the words. Digits, `Enter` and `n` act at once, so an answer is never held. A note, a mark or a spelling asked for while an answer is on its way is done when the next item is shown. The browser hands each key to this guard, and a test strikes keys through the page's own listener to hold that it does.
- **The first undo of a sitting** that would take back an answer of an earlier one asks for the key again.
- Text from a file reaches the screen as text, never as markup. An address is shown to copy and is never a link. Under the note: "A note may be published. Write nothing about yourself or anyone else."
- **The note asks the browser to check no spelling**, to correct nothing and to translate nothing. Some browsers check spelling on their maker's servers. That is no request the page makes, so no policy of the page could stop it. What a browser then sends has not been watched: section 10.
- The map is drawn on a canvas, from the layers, with a flat projection about the middle of the item. No map library is used, so none is copied or fetched: the website's library draws tiles, and the desk has none. It is measured after the line under it is written, is drawn again when its box changes size, and then stays where the person put it.
- **After a move the heavy outline is the border as it now stands.** It is made from the cells the area holds: every edge that one cell of the area has and no other cell of it shares. The outline as drafted is drawn thin and broken, for every area that lost or gained a cell. Two cells share an edge only where both give the same two points, which is so of cells cut from one file, and has been seen on the made-up city alone.
- **The place asked about is marked.** A ring is drawn where a record puts the name, and the name is printed at it in heavy letters where no layer of records is drawn. The town centre whose name is asked about is named in heavy letters too, clear of the cross. A name is printed once: an area of the same name is named at its seed alone.
- **A mark says by its look what the doubt is.** A draft says in `marks.csv` what to mark on the map of a border. A cell in doubt has a ring where its margin is under 10%, a square where it lies outside the main borough, a square on its point where it lies beside an area whose seed is close, and a triangle where it is cut off from the largest piece. A cell under two doubts has both marks, one round the other. A stretch of the border that follows no line is drawn over the cells in a heavy dotted line: the lengths that the two cells of each such side share. The seed that stands close has two rings round it and a broken line to the seed of the area asked about. A town centre that a flag names is named in heavy letters, as the one whose name is asked about is. The top left corner of the map says in words what each look means, for the looks that are on the map and no other.
- **A code does not crowd the area.** At the scale an item opens at a cell in doubt shows its mark and no code, but for the cell under the cross: a person puts the cross on a mark to learn which line is about it. Once the map is twice as close, every mark in view shows its code.
- **The cells in doubt are counted once, by the draft.** The first line of a border says how many cells it holds and how many lie on a border, and counts no cell in doubt. The draft's line "In doubt" says how many there are, the rule in words, and how many are under each reason. A margin of a hundred or more is said as so many times as far, and never as a percentage.
- **No name lies under the cross.** The name of an area, of a record asked about and of a cell a line is about is moved down or up until it is clear of the cross and of every other name. A ward, a road and a town centre are left out where they would lie over a name.
- What decides anything is a pure function in `logic.mjs` or `map.mjs`, tested with `node --test`. No browser is needed to test it.

## 6. What is drawn behind a border

By areas sections 3.2, 9 and 13: only layers from sources registered for `gazetteer`, and never a basemap. It holds for every queue with a map.

| Layer | Drawn as | Source | How the desk gets it |
|---|---|---|---|
| `cells` | Filled, in the colour of its area | `ons-output-areas-2021` | The areas build cuts it for each borough, with a margin of 500 m. `fill` asks `Registry.require(id, gazetteer)` for every source a layer names, then copies the file |
| `areas`, `boroughs` | Outlines, as drafted. `boroughs` is in the group `all` | Made from `cells` and `ons-oa21-lsoa21-msoa21-lad22-lookup` | The same |
| `wards`, `centres` | Thin outlines. Hatched outlines | `os-boundary-line`, `gla-town-centre-boundaries` | The same |
| `roads`, `names` | Lines by class. Names as text | `os-open-roads`, `os-open-names` | The same |
| `seeds`, `records` | Points | The draft, and each publisher's own record of a name | The same |

Never drawn: OpenStreetMap, or tiles of any kind. Stations, parks and rivers, until the registry gives `dft-naptan`, `os-open-greenspace` and `os-open-rivers` the use `gazetteer`. MSOA names while `hoc-library-msoa-names` is gated. Imagery. A line written by a model. A figure about residents, a price, a crime rate or a deprivation rank. On the made-up city every layer is made from the synthetic release, and every id begins `syn-`.

| What could slip in | What stops it | Held by |
|---|---|---|
| A layer from a source without the use | The gate is asked about every source a layer names, before any layer is copied | `test_no_layer_is_from_a_source_without_the_use` |
| A record of a source its layer does not name, as one taken from OpenStreetMap | The fill step refuses a record that does not say which source it is of, or is of a source its layer does not name. The page holds each record to its own tripwire, and credits only the sources the records drawn are of | `test_a_record_from_a_source_its_layer_does_not_name_is_refused` |
| A name from a gated file, in the evidence of a cell | Each name in the evidence has the source it comes from: `roads` from `os-open-roads`, `ward` from `os-boundary-line`, `centre` from `gla-town-centre-boundaries`, `msoa` from `hoc-library-msoa-names`. On a real draft the gate is asked about each that any row uses | `test_a_name_from_a_source_that_is_gated_is_never_shown_beside_a_border` |
| Words about who lives somewhere, in a rubric or in evidence | The fill step holds every draft to a list of such words, and names the file and the row. The name of a place is left alone: a place may be named for a word on the list, and the founder reads every name | `test_a_rubric_about_who_lives_somewhere_stops_the_fill`, `test_no_item_holds_a_field_about_residents` |
| A name that says who lives there | It is flagged in `names` as `describes_residents`, by the build or by the fill step, and put to the founder: areas section 6 | `test_a_name_that_holds_a_word_about_who_lives_there_is_flagged_for_the_founder` |
| The made-up city where a build of London looks | The made-up city is filled only into a folder whose name ends `-synthetic`, and every row of every file under `out/` says whether it is made up | `test_the_made_up_city_is_filled_only_into_a_folder_named_for_it`, `test_every_file_made_from_the_made_up_city_says_so` |

## 7. Where it lives

`tools/desk/`, and nowhere else. `make ci` already tests, lints and type-checks `tools/`, so no settings file changes. One command starts it:

```
make desk                  the desk on 127.0.0.1:8765, as r1. KEEP=FOLDER, REVIEWER=r2 and ARGS="--port 8766" change that
make desk KEEP=FOLDER      the same, with the second copy of every decision in a folder of your own
make desk-check            the desk's tests, and the page's with node --test
make desk-take DRAFT=...   take a draft of the areas to the desk: copy what it hands the desk to data/raw/desk/draft, and fill the queues
make desk-fill ARGS=...    fill the queues from a draft folder: --from data/raw/desk/draft --data data/raw/desk
make desk-compile ARGS=... make a build's files from the lines: --data data/raw/desk --gazetteer gazetteer/london
make desk-publish ARGS=... make the copy of the decisions that may be committed: --to gazetteer/london
```

`make desk` serves `data/raw/desk/` when it holds `items/`, and then needs a folder outside the repository for the second copy: the one section 3 names, or `KEEP=FOLDER`. If not, it fills `data/raw/desk-synthetic/` from `data/fixtures/synthetic/` and serves that. Both are under `data/raw/`, which git ignores. `<data>` holds `draft/`, `items/`, `layers/`, `decisions/`, `decisions-private/`, `gazetteer/` for the made-up city, and `out/`. `fill` never touches the decisions. `make desk` needs Python alone. `make desk-fill` on real files needs `make setup`, for the licence gate.

## 8. Who builds what

Three parts, and no file in two of them. No part's tests need another part's code: (a) tests on item files a test writes, (b) on answers written to the shape of section 4, (c) on the synthetic release. Tests come first and are named for what they protect, as `test_a_line_is_on_disk_before_the_server_answers`.

| Part | Owns |
|---|---|
| (a) Records, server, compile, publish | In `tools/desk/`: `__init__.py`, `__main__.py`, `cli.py`, `records.py`, `server.py`, `compile.py`, `publish.py`, `AGENTS.md`, `CLAUDE.md`, `tests/test_records.py`, `tests/test_server.py`, `tests/test_compile.py`, `tests/test_publish.py`, `tests/test_cli.py`. The four targets in `Makefile`, a job `desk` in `.github/workflows/ci.yml` that runs `node --test tools/desk/page/test/`, and the row for `tools/desk/` in the root `AGENTS.md` |
| (b) The page | `tools/desk/page/index.html`, `desk.css`, `desk.mjs`, `logic.mjs`, `map.mjs`, and `page/test/*.test.mjs` |
| (c) Filling the queues | `tools/desk/fill/__init__.py`, `synthetic.py`, `draft.py`, `layers.py`, `gate.py`, `tools/desk/questions.json`, and `tools/desk/tests/fill/` |

| Between | Interface |
|---|---|
| (c) to (a) | `desk.fill.run(source: Path, data: Path, *, synthetic: bool) -> int`, called by `cli.py`. Only `gate.py` imports outside the standard library: `burro_pipeline.registry`, for real files |
| (c) to (a) and (b) | `questions.json`, with the queues in the order of the work: for each queue `id`, `title`, `text`, `rule`, `view`, `adds`, `after` as the queues it waits on, `open_to` as `founder` or `all`, `public`, `answers` as `{code, label}`, and `flags` as words by code. A queue that adds `move` has `moved`: the `text` and the `answers` it asks in once a cell is moved. `ratings` has `covers`: `by`, `code` and `label` of the answer given to a whole part. `names` has `set_aside`: the `answers` that turn a name down, the `mark` of such an answer, and for `cells` and for `names` the words `short`, `words` and `saved`. It holds section 2's questions and codes as written, and (c) writes each label in plain words. Flag codes: `margin_under_10`, `least_compact`, `two_boroughs`, `two_centres`, `one_publisher`, `seeds_close`, `follows_nothing`, `size_unlike_neighbours`, `two_pieces`, `both_banks`, `seed_outside`, `no_receipt`, `same_name_elsewhere`, `describes_residents`, `look_hard`, `names_another_area`, `no_reference`, `two_areas`, `unsure_match`, `near_the_edge`. The areas build holds its own words for a flag to these, in a test |
| (c) to (a) | `<data>/items/<queue>.jsonl`. Line 1: `desk` (1), `queue`, `question`, `synthetic`, `made_on`, `made_from` as `{source_id, file, sha256}`, `count`. Then one item a line, in the order of section 1 |
| An item | `id`, `rev`, `group`, `title`, `lines` as `{label, value, source_id}`, `text` as `{before, body, after}` or null, `map` as `{bbox, focus, layers}` or null, with `marks` as `{cells, sides, seeds, centres}` where the draft marks anything: `cells` gives for the code of each cell in doubt the flags it is under, `sides` pairs of codes, `seeds` ids of areas and `centres` names of town centres, `picks` as strings or null, `flags` as codes, `fill` as the words for the question, `preset` as what the page copies into `detail`, with `proposed` as the code of the answer the draft proposes, `holds` as what an area holds that the desk cannot take from under it, `fits` as the rule that would settle the item, and `leans_on` as the rule the item leans on where that rule leans on others. `group` names the folder of the item's layers, and is what `g` chooses: the borough's name in lower case with hyphens, `all` for `know`, and the article or the kind where there is no map. `rev` is the first 12 hex digits of the SHA-256 of the item without `rev`, keys sorted. For `borders`, `whole` and `ratings` it is of the item's id, its flags, its rubric and its cells with what placed each, and of no name. The `preset` of a rule holds `settles`, a digest of every item the rule would settle as each stands: so a rule is open again when that list has changed, and a yes is given to one list and to no other. It holds `leans_on` as the list of rules the rule leans on, where it leans on any, and `drawn` as the ids of the items it shows, in the order of their lines, each labelled "Drawn at random, 3 of 10" |
| (c) to (b), through (a) | `<data>/layers/<group>/<layer>.geojson`: a FeatureCollection in WGS84, longitude first, 6 decimals, with a member `desk` of `layer`, `group`, `source_ids`, `synthetic`. Each feature has an `id`. Properties: `cells` `area`, `colour` (0 to 11), `borough`. `areas`, `boroughs`, `wards` `name`. `centres` `name`, `class`. `roads` `class`, `name`. `names` `name`, `kind`. `seeds` `area`, `name`. `records` `source_id`, `as_written`. A draft that draws no layer `records` draws a publisher's record of a name as a point of `names`, under the record's own id: the fill finds the point there, and the item's `map.focus` holds it as `at` |
| (b) to (a) | The routes of section 4, and the line of section 3 |
| The draft folder, read by (c) and by `compile` | The four files of areas section 5, as drafted. `review_state` of `areas.csv` is `drafted`, or `named_by_rule` for an area whose name stands by a rule the founder has decided already: the desk makes no item of such a name, unless it carries a flag. `flags.csv`: `queue`, `item`, `flag`. `layers/`. `kinds.csv`: `record_id`, `source_id`, `kind`, `name`, `category`, `upstream`. `figures.csv`: `area_id`, `feature_id`, `value`, `unit`, `source_id`, `vintage`, `flag`. `sentences.jsonl`: `page_id`, `revision_id`, `title`, `section`, `sentence`, `text`. `claims.jsonl`: the rows of researcher section 5. `commons.csv`: `name`, `record_id`, `match`, `kind`, `way_in`. `rubrics.csv`: `vibe`, `rubric`. `area_sources.csv`: `area_id`, `source_id`, `qid`, `page_id`, `title`, `role`, one of `own`, `alias`, `thing`. `lines.csv`: `queue`, `item`, `label`, `value`, `source_id`, what the draft says beside an item: the desk keeps the first line of its own and shows these under it, asks the gate about every source a line names, and refuses a line of an item it does not make. A line of the queue `rules` is of a rule, by its code, and is shown before the items the rule shows. One labelled `Already decided` says what the founder has decided of the rule, and is shown under what the rule would settle. `order.csv`: `queue`, `item`, `rank`, the order to look in, from 1: an area under `borders`, a borough under `whole`. `marks.csv`: `queue`, `item`, `flag`, `kind`, `what`, what to mark on the map of a border: `kind` is `cell` for a cell of the item that is in doubt, `side` for the cell of the item and the cell beside it where a border follows no line, `seed` for the area whose seed stands close, and `centre` for the name of a town centre, and `flag` is a flag the page has words for. The desk refuses a mark of an item it does not make, a cell of another area, and a side that is not between the item and another area. `rules.csv`: `rule`, `queue`, `gives`, `says`, `goes_wrong`, and `leans_on` as the rules a rule leans on, with a space between them. `rules_items.csv`: `rule`, `queue`, `item`, with each item under one rule alone, and `leans_on` as the rule the item leans on, which is one of those its rule names |

`synthetic.py` makes a draft folder from the synthetic release, and `draft.py` turns any draft folder into items, so the made-up city and London take one path. The synthetic release holds no cells, no sentences and no claims: `synthetic.py` cuts cells as a grid, and makes up sentences that name only the made-up areas, with one planted for each answer.

## 9. Left out on purpose, and what the founder decides

The plans ask more of a person than the desk can take. What is in no queue is done by hand, or waits.

| Left out | Why | Holds up |
|---|---|---|
| Opening one source in ten (15 h), and reading each finished block whole (8 h) | The same shape as `claims`. Each is one fill step, written when claims exist | M8 |
| The counts made by hand in 20 sampled areas, for the amenity vibes | The shape of `commons`: a name, what the file holds, three answers and a note. It waits on the counts themselves | M6 |
| Residents marking each line of their own area's portrait, and the lists of traps | They need the portrait, which no release holds yet, and people who are not at the desk | M6 |
| The 37 licence items to open, save and confirm (6 h), and the five pages of task 8 | The shape of `commons` too. Each is a page opened in a browser and a file saved, which the desk does not do | M7 |
| The census block checked by hand | Rule 8. Figures about residents stay out of the desk, so none can stand beside a border | M4 |
| Raters and residents who are not at the desk | They need a host, a login and a privacy notice, which no design holds. The desk takes ratings from whoever sits at it | M6 |
| The gym operator list, Richmond's 18 wards, the reader's golden queries | No source yet. 18 rows to edit by hand. `evals/` has its own format | |
| A basemap, and a map library | Areas section 3.2. The desk draws what it may show, and asks no other host for anything | |
| Sign-in, several reviewers at once, a database | One person at one machine. A file for each reviewer is enough | |
| Editing a name, drawing a shape, splitting a cell | Burro never respells a name, and a border is made of whole cells | |
| Taking the ground from under an area, and making an area of another name | Only the areas build gives an output area to an area, and an area its id. The desk saves the answer, says at once that it waits, and the draft is made again from `out/names.csv` | M3 |
| A screen for each item a rule would settle | The founder is shown ten, drawn by a fixed shuffle, and may open each. Every item is in the draft's own table of what each rule would settle, which the rule names, to skim | M3 |
| A model's line beside an item. The salted hash of the ratings. The audit of a moved border | london-data section 14, rows 14 and 13, and vibes 6.2. Each belongs to the part that reads the lines | |
| Asking first, once for an area, whether it is known | One key on any vibe of the area says so, which is one key in place of eight and asks nothing of a rater who knows the area | |
| Saying before a fill how many answers it opens again | A border is no longer opened again by a name. A fill that changes cells opens the borders of those cells again, as it should, and says nothing before it does | M3 |

| The founder decides | Recommended |
|---|---|
| Where the second copy of every decision is kept | Decided on 2026-09-24: a folder in the home folder, outside every repository, that a backup takes. Section 3 names it. The desk does not serve real data without one |
| Are the lines of the seven public queues committed, under `gazetteer/london/decisions/` | Yes, by `make desk-publish`, once its notes are read. A note is public from then on. The copy says the day and never the hour |
| May `out/private/to_look_at.csv` be shown to anybody | No. It holds the notes of private queues. It lists what the founder is to look at again |
| The rubric for each vibe, in words about streets, buildings and places | The founder writes all eight before the first rating. The fill step refuses a rubric that asks who lives somewhere |
| May a rater be given the desk and the layers to run themselves | Not in this version. It waits on the notice and the host |
| The 20 names for `commons` | From what the founder knows, and from no map |
| Is a third of a second too long to hold a letter | Decide at the desk, in a browser. It is `HOLD_MS` in `logic.mjs` |
| Which of the rules a draft puts are adopted | None, until the founder says yes to each at the desk. The desk adopts none by itself, and every yes can be taken back. What the founder has decided already is said on each rule, and is asked of nobody again: section 14 |
| Does a name that a rule accepted count as read | The desk applies it as the founder's answer, because the founder adopted the rule, and names the rule in every line and in `out/names.csv`. Whether a build ships such a name is for the areas design to say |
| Is `j` the key for the next flagged item | Decide at the desk, in a browser. It is one line of `keyAction` in `logic.mjs` |
| Does the desk trust every program on the machine | Yes, for one person at their own machine: section 4. If the machine has more than one account, the token goes in the address and out of `/api/state` |

| Asked of | Change |
|---|---|
| Areas design | Section 9 names a static page and a patch file. The desk replaces both: a move holds the patch's four columns. The draft gives each candidate its `area_id`, and an id that is dropped is never used again |
| Areas design | Section 6 held that a person reads every area name. A rule the founder adopts settles names that nobody read one by one. The design says what a build makes of a row of `out/names.csv` whose `rule` is set. Since 2026-09-24 it says which names stand with no person reading them: areas section 19 |
| Areas build | `lines.csv`, `marks.csv`, `order.csv`, `rules.csv` and `rules_items.csv` in the draft folder, as section 8 gives them. A flag it raises has its words in `questions.json`, or the fill stops |
| Areas build | The draft folder of section 8, in WGS84. The desk converts no coordinates. A name that holds a word of the researcher's list of group words is flagged `describes_residents` in `flags.csv`. Each record of the layer `records` names a source that its layer names |
| Research run | `area_sources.csv` in the draft folder, before any page is fetched. It reads `out/articles.csv` for the rows a person confirmed, and `out/private/golden.jsonl` and `out/private/claims_review.jsonl` from where they now are |
| Registry | Whether stations, parks and rivers gain `gazetteer`, as areas section 13 asks. Which use a sample of `overture-places` is read under: the desk asks for `scoring`. Whether `hoc-library-msoa-names` is approved: until it is, a draft that names an MSOA in the evidence of a cell is refused |
| Researcher and claims | `Reviewer` holds `founder` and `second`. A third reviewer has no role to be written as |
| Hosted CI | The job that runs the desk's Python tests needs Node, or the test of the page against the desk is left out without a word |

## 10. What only a browser can show

No test opens a browser. `tests/test_walk.py` asks the server what the page asks, and `tests/test_page_at_the_desk.py` runs the page's own code against the server with a stand-in for the browser. Neither lays a page out or draws a pixel. A person walks these, on the made-up city, at 1280 by 720 and at 1440 by 900, in light and in dark.

**What the first sitting was.** On 2026-09-24 a program opened the page in Chrome and struck keys, in every queue, in windows of 1280 by 720 and 1440 by 900. Its tab was out of view, so no frame reached a screen unless a picture was taken. It saw the map drawn in every queue that has one, a cell moved by keys and by a click, the page come back where it was left, and a second tab told that the item was answered already. It found thirteen faults, which were mended the same day and are listed below to be looked at again. It did not see: the desk stopped in the middle of an answer, the wheel or a trackpad on the map, the address typed into the address bar, dark, any browser but Chrome, a screen reader, or a person's hands.

**Look at these again, in this order.** Each was mended with no browser open. The tests hold what each does, and none holds how it looks.

| Look at again | What would be wrong |
|---|---|
| A sentence typed with the note shut, in any queue: "this is not a hall", then "so it is", then `s` alone | A line is written to the file of decisions. The note opens. The line under the top line does not say that words were taken for words. `s` alone does not skip, or skips before a third of a second |
| Names, Borders, Ratings and Claims at 1280 by 720, and again at 1440 by 900 | An answer, the note or the mark is out of view. The name of the item is printed twice, or not at all. What was saved is not under the top line, or moves the map when it changes. The spellings or the cells moved are below the evidence. "More below" is not shown when there is more, or `.` and `,` do not page it. The question moves up or down from one item to the next |
| The rule, on the first item of a queue and on the second | It is shut on the first item where there is room for it. It is open on the second. In Ratings at 1280 by 720 it covers an answer |
| `7` in Ratings, and then `u` | One `u` leaves a vibe of the area as not known. The line does not say how many answers were taken back. The top line does not count the area as open again. The line under the top line flickers while the area is answered |
| A cell moved in Borders, and one in Whole boroughs | The heavy line still runs where the draft ran. The heavy line has gaps at its corners, or runs between two cells of one area. The thin broken line of the draft is not seen, or is taken for a ward |
| The address of the desk, clicked in a chat or a page, and typed | A click shows JSON, or shows the small page with no link. "Open the desk" does not open it. The address typed does not open the desk at once |
| The first map of a sitting, and the window made smaller and larger | The first `+` does nothing. The cells are not square. The map goes back to the whole item when the window changes size |
| Whole boroughs, as it opens | An area has no name. A name lies under the cross, or over another name. A name is so far from its point that it reads as the name of the next area |
| Shift with an arrow, with a cell in the hand | The cross cannot be put on a cell that an arrow alone steps over. Shift with an arrow marks text, or leaves the item |
| The list of queues and the list of keys, at 1280 by 720 | The twelfth queue, on `=`, or the line under the list is out of view. The keys are not in two columns, or a row is cut in two |
| `f`, then a note, then an answer | The line does not say "with a note" and "second reviewer asked" |
| Articles, Claims and Ratings while Names is not done | The page says that a name opens a border again |
| Figures, after `make desk-fill ARGS="--made-up"` | An area beside the one asked about is not said to be beside it |
| The browser's console, on the first load | A fault for the lack of an icon. A file the content security policy refused |

**Not yet seen by anyone.** Each is a guess about hands or about a browser that no test can settle.

| Look at | What would be wrong |
|---|---|
| The desk stopped while an answer is on its way | "Not saved" is not seen at once, in the line under the top line. The browser does not ask before the page is closed. The answer is not sent when the desk is back |
| The list of requests while a note is typed, in each browser | Any request to a host but `127.0.0.1`. The note asks for no spelling check, and what a browser then sends has not been watched |
| `s`, `u`, `n` and `f`, struck as in real work | The third of a second for which a letter is held is felt as a key lost. `n` and then the note, typed fast, loses its first letters or is taken for words |
| A sentence typed slowly with the note shut, a letter every half second | Each letter is still a key: only fast words are known for words |
| `Enter`, after a click of the mouse on an answer, and after `Tab` | It gives the answer the keyboard was on and not the one proposed, or the one proposed when the person meant the button |
| The colours of two areas side by side, to an eye that does not tell red from green | Two areas are one colour. In Whole boroughs areas that meet at a corner were seen in one red |
| The flagged areas of a whole borough | They are listed beside the map and not marked on it. The item gives their names and not their ids, so the page cannot find them: it waits on the step that fills the queue |
| A name of an area with ground, in Names, at 1280 by 720 | The line that says the answer waits pushes an answer, the note or the mark out of view. What to do is not open on the first such item, or is open on the second. "(waits)" breaks an answer over two lines so that its key is lost |
| A rule, in Rules | The rule is set too large to be read whole. The ten items are below the fold, and "More below" is not shown. `.` and `,` do not page it. The words of what could go wrong are taken for the rule |
| Yes to a rule that settles over a hundred items | The page says nothing for longer than a second, or says "Not saved" though every line is on the disk |
| The bottom line of keys, with `j` on it | It wraps to two lines at 1280 by 720 |
| `j`, in Borders, after the last flagged border of a borough | It stops at a border that is not flagged. It does not go on to the next borough. The line under the top line does not say where it went |
| An item that a rule settled, looked at with `[` and `]` | It does not say which rule settled it. The answer the rule gave is shown as the person's own |

**What any sitting looks at.**

| Look at | What would be wrong |
|---|---|
| The whole screen, in each of the eleven queues | The page scrolls. The question or an answer is out of view. The bottom line of keys wraps to two lines, or is cut |
| The top line | It is not the first thing seen. "MADE-UP CITY" and "REAL DATA" look alike. It is covered by a list |
| The map, in `borders`, `names`, `whole`, `ratings` and `know` | It is blank, blurred or stretched. Two areas side by side are one colour. A name lies over another. The cross is not in the middle. The item is not the thing the eye finds first. The ring round a cell another reviewer moved is not told from the dot on a cell of one's own |
| A cell taken up and put down, by click and by `m` | The cell taken up is not the one clicked. The cell does not change colour when it moves. Dragging the map moves a cell |
| The wheel, a drag, `+`, `-`, `0` and an arrow | The map jumps, or is slow. Time a whole borough of London when there is one: the made-up city has 1,115 cells, and London has 26,369 |
| The note | A letter typed in it answers the item. `Enter` or `Esc` leaves the keyboard in the wrong place. A key struck after it is lost. `Enter` struck twice answers the item |
| The lists of `q`, `g` and `?` | The keyboard is not in the list when it opens. `Esc` does not close it. The page behind it takes a key |
| A key held down, and a key struck twice | Two items are answered. The quarter of a second in which a key is dropped is felt as a key lost |
| The tab out of view, and the machine asleep | The clock runs on. The page does not come back |
| A border of London once there is one, after a cell is moved | The heavy line runs between two cells of one area, because the two cells do not give the same points for the edge they share |
| Text at 200%, and a window 1024 wide | Words are cut or lie over each other |
| The browser's console and its list of requests | An error. A request to any host but `127.0.0.1`. A file the content security policy refused |
| Safari, Firefox and Chrome | The list does not open, the canvas does not draw, or a key does something else. `?` and `+` need Shift on most keyboards, and `[` and `]` are not one key on every keyboard |
| A screen reader, and the keyboard alone | The item, the question and what was saved are not said. A control cannot be reached by Tab |
| Forty minutes of real work | The pace on the top line is wrong. The hands leave the keyboard. A word on the page is read twice to be understood |

## 11. What the first draft of London asked, and what was done, 2026-09-24

The areas build made a first whole draft of London for the desk, and its makers could not touch the desk's code. Areas section 18 and [the report of the first draft](../research/data/m3-first-draft.md) list what they asked. This is what was done. Every count is over all of London, was made from the draft as the code below makes it, and names no place. Nothing of the draft is in the repository, and nobody has looked at any of this in a browser.

| Asked | Done | Held by |
|---|---|---|
| Say on the page at once that an answer will be set aside | The item says what its area holds. The page says before the answer is given that it waits, and what to do. The top line, what was saved, `borders`, `whole` and `compile` say it too | `test_the_desk_counts_the_names_turned_down_that_wait_for_a_new_draft`, and the page's "before the name of an area with ground is turned down" |
| Read `lines.csv`, so that no step lays the lines over the items | The fill reads it. The step of the areas build that laid them over is removed | `test_the_lines_of_the_draft_stand_under_the_first_line_of_the_desk` |
| Words for seven flags | The desk has words for all twelve flags of a border, for a whole borough too, and for a name that rests on a file with no receipt | `test_every_flag_the_areas_build_raises_has_its_words`, and in the areas build `test_the_desk_has_the_words_of_every_flag_this_part_can_raise` |
| A publisher, and not an id, beside a record | A record is labelled with its publisher and what the file is called, as the registry gives them. The page names the id after the value | `test_two_files_of_one_publisher_are_shown_under_the_name_of_that_publisher` |
| Names in the order of the boroughs a reviewer knows, and a borough finished before the next | Names and borders are filled borough by borough, the most at stake first, and are offered by what the reviewer knows | `test_the_borough_with_most_at_stake_comes_first_and_is_finished_before_the_next`, `test_names_are_offered_in_the_order_of_the_boroughs_the_reviewer_knows` |
| A key for the next flagged item | `j` | The page's "one key goes to the next flagged border" |
| The kind of place, the road records, the size, and a file with no receipt | Each is a line of the item, written by the draft in `lines.csv` | In the areas build, `test_a_name_says_the_kind_of_place_its_publisher_gives` and the three after it |
| The rules put to the founder | A queue of their own, first in the order | `tests/test_rules.py`, `tests/fill/test_rules.py` |

| Counted on the draft | Before | Now |
|---|---|---|
| Names at the desk | 780 | 783. Three names that stand inside two areas were each asked about once, and the second place was left out |
| Borders flagged at the desk | 230 | 279 |
| Lines of a name that say a kind of place, road records or a size | 0 | 782, 691 and 488 |
| Borders that say which file has no receipt | 0 | 355 |
| Names read before a first borough is finished | More than 488: every area of London came before any other name | 44, of the borough that holds the most at stake |
| Rules put to the founder, and what they would settle | 8, in a table the desk did not read | 8 items. 438 names and 26 borders. The eighth rule settles a border that is flagged only for lying in two boroughs: the desk now shows every flag about a border, so 13 borders that carry another flag are no longer settled by it |
| Names a rule would turn down that are areas with ground | Not said | 8, of two rules. Each rule says so on its own item |

**The draft made again, and the queues filled again.** This was driven once on the draft of London, with answers that are nobody's decisions: three rules adopted, six areas turned down by one of them, the draft made again from `out/names.csv`, and the queues filled again over the same decisions. The draft then held 481 areas. Every answer to an item that had not changed stood, and 6 of 127 names a rule had accepted were asked again because their items had changed. The six names turned down were no items of the new queue, and are kept in `out/names.csv` with `asked_today` as `false`, so that the next draft leaves them out too. All eight rules were asked again, because each would settle another list than before, and nothing a rule had settled was taken back while it waited for its answer.

**What was not done.** The desk still cannot make an area of another name: section 9. A name that was turned down and is no item any more cannot be given back at the desk: its line is taken back with `u` if it was the last, or with its rule, and otherwise the file of decisions for the draft is written by hand. Nobody has timed a sitting. The page has been looked at since by a program, and by no person: section 12.

## 12. The sitting on the draft of London, 2026-09-24

A program opened the page in a browser on the first draft of London, in a window of 1440 by 900, in a tab of its own. It read the eight rules, the first thirty names and the first ten flagged borders, and gave no answer: no line was written. Every request the page made was to the loopback address, and the console held no fault. It did not see dark, a window of 1280 by 720, any browser but one, the wheel, a drag, a click on the map, a note, an answer, an undo, Whole boroughs, Boroughs you know, or a person's hands. Every count is over all of London and names no place.

| Found | Mended | Held by |
|---|---|---|
| The top line said that the data is real, and not that it is a draft that nobody has checked | The top line, every list and the page for an address opened from elsewhere say so | `test_real_data_is_said_to_be_a_draft_that_nobody_has_checked_wherever_it_is_said` |
| In Names a label as long as a publisher and the name of its file left the value a few letters to the line. What is known of the first name was 3,760 pixels high in a box of 128 | A label begins the line of its value | The page's "a value of what is known has the width of the column, however long its label is" |
| On the first name of a sitting the mark for a second reviewer was cut by the keys: the answers were measured before the line that says there is more was shown | The rule gives way again once that line is shown | The page's "the rule is shut where the line that says there is more to read pushes an answer out of view" |
| Of a name proposed as a smaller place, nothing on the map said where in the area the place is. The draft draws no layer of records | The fill finds the record's point in the layer of names. The page rings it and names it. 691 of the 783 names say where a record puts them | `test_a_name_is_shown_where_its_record_puts_it_in_a_draft_that_draws_no_records`, and the page's "where a record puts the name asked about is ringed and named, though no layer of records is drawn" |
| Of a name that only a town centre writes, two town centres were hatched in the area and neither was named | The town centre whose name is asked about is named, clear of the cross | The page's "the town centre whose name is asked about is named, though it lies under the cross" |

**Read, and found fit to decide from.** Each rule says in words what it would settle, how many items, what could go wrong, how many wait for a new draft, and ten of the items. A border shows its cells in the colour of its area, the borough line, the wards, the town centres hatched, the roads and their names, and a ring with its code on every cell a line is about. The line of a cell says its margin, its second choice, its borough, its ward and its streets.

**Still wrong when that sitting ended.** Fourteen things, of the rules, the names and the borders. Section 13 says what was done about each, and what is still left.

## 13. What that sitting left, and what was done, 2026-09-24

Each thing the sitting of section 12 left as wrong was closed the same day. No browser was open. Each change is held by a test, the draft was made again from the fetched files, the desk was filled from it and asked over its own port, and the page's own code that draws a map was run over every border with no screen. So what each change does is known, and how it looks is seen by nobody yet. Every count is over all of London and names no place. The ground of the draft did not change: every output area is in the area it was in.

| Was wrong | Now | Held by |
|---|---|---|
| The fifth rule settled 40 names whether or not the rule each leans on was adopted | The draft names the rules it leans on, and for each of the 40 the one it leans on: 6 on the first rule, 13 on the second, none on the third, 21 on the fourth. The desk settles a name only where both rules are adopted, in whichever order. Adopted alone, the fifth settles none. Its screen says which of the four stand adopted | `test_a_rule_that_leans_settles_nothing_until_the_rule_its_item_leans_on_is_adopted`, and the page's "a rule that leans on others says which of them stand adopted" |
| The ten items a rule shows could not be opened from it, and the draft's table of them all was not named | `o` opens the first, `]` and `[` go through the ten, and `o` comes back. Each rule names the table | `test_each_item_that_is_drawn_can_be_found_by_the_page_to_open_it`, and the page's "an item that is drawn is opened from its rule" |
| "More below" stayed once the last line was in view | It goes, and comes back when a person reads back | The page's "the line that says there is more to read goes when the last line is in view" |
| Nothing said what a point is. A town centre of another name was named by its id alone | The line of points says what a point is, in one sentence, and names the town centre and the ward as their files write them | In the areas build, `test_where_points_are_shown_the_line_says_in_one_sentence_what_a_point_is` and the two after it |
| The draft gave two or three distances for what read as one thing | Every distance says what it is from and what it is to, and one length is written one way | `test_a_distance_says_from_what_to_what_and_one_thing_has_one_distance` |
| The ward said to carry a name was at times another than the ward the item lists | The ward named is one that writes the name where one does. Of 371 names a ward carries, 284 name a ward the item lists, and 87 a ward whose label only holds the name, which says so | `test_the_ward_that_gives_the_point_is_one_that_writes_the_name_where_one_does` |
| "No receipt" did not say which of the name, its points and its seed | It says which | `test_what_rests_on_the_file_with_no_receipt_says_which_of_the_three_it_is` |
| 58 names with a line "Look hard" carried no flag, so `j` passed them | Each carries the flag `look_hard`. 674 of the 783 names are flagged, where 616 were | `test_a_name_with_a_mark_to_settle_is_flagged_so_that_the_desk_stops_at_it` |
| "An area" was offered on a name proposed as another name | It is not offered there, and every other answer keeps its key | The page's "the answer that makes an area is not offered on a name proposed as another name" |
| An area's item did not list the other names the draft puts in it | It does, by what each is offered as. 190 areas list some, and 298 say that there is none | `test_an_area_lists_the_other_names_the_draft_puts_in_it_by_what_each_is_offered_as` |
| Two counts of the cells under 10% stood side by side and differed. The desk counted the cells on a border with such a margin, and the draft every cell with one | The draft counts the cells in doubt once, with its rule in words and how many are under each reason. The desk counts none. All 4,955 cells in doubt are under a reason | `test_the_cells_in_doubt_are_counted_once_and_every_one_is_under_a_reason`, `test_the_first_line_of_a_border_counts_no_cell_in_doubt` |
| A margin was shown as up to 999% | From a hundred it is said as so many times as far: 328 cells | `test_a_margin_of_a_hundred_or_more_is_said_in_words_and_not_as_a_percentage` |
| A border flagged for following no line, or for a seed close to another, marked nothing | The draft hands the desk `marks.csv`. 2,703 sides are drawn on the 60 borders flagged for following no line, and the seed that stands close is marked on 44 | `test_the_desk_is_handed_the_marks_of_every_border_and_each_is_of_a_flag_it_has_words_for`, and the page's "a border flagged for following no line has each stretch that follows none drawn over it" |
| Every ring was alike, and the codes crowded the area | A mark says by its look what the doubt is, and a corner of the map says what each look means. At the scale an item opens at only the cell under the cross shows its code | The page's "the mark on a cell in doubt says by its look what the doubt is" and "at the scale an item opens at a cell in doubt has a ring and no code" |
| Two town centres that a flag names were hatched and not named | They are named: 12 town centres on 6 borders | The page's "a town centre that a flag names is named on the map" |

**Look at these in a browser, in this order.** Each is a change to what is drawn or laid out, made with no browser open. The order is the order of the work, so that each is met as the desk is worked. A place in a queue is its place before any borough is marked as known.

| Look at | What would be wrong |
|---|---|
| Rules, the first rule. Press `.` until the last of the ten items is in view, then `,` | "More below" is still shown at the end, or is not shown again after `,`. The answers move up or down as the line comes and goes |
| The same rule. Read the line "To open them", then press `o` | The line is not above the first of the ten. The item does not open with its map. The line under the top line does not say "Drawn for the rule", which of the ten it is, and that nothing is decided |
| With that item open: `]` nine times, `]` once more, a digit, `Enter`, `s`, `u`, then `o` | `]` leaves the ten. A key writes an answer: the line must say that nothing is decided here. `o` does not come back to the rule, or the rule is not the one that was left |
| Rules, the fifth rule, before any rule is adopted | The line "Leans on" is not under "Would settle". The line "As the rules stand" does not say that none of the four is adopted and that a yes settles nothing. The two lines push the ten items so far down that they are not found |
| The fifth rule, once you have answered the four before it as you mean to | "As the rules stand" does not name the rules you adopted, or counts other than the items that lean on them. After a yes, what was saved does not say how many were settled and how many wait |
| Names, the first name. Read what is known to its end | The line of points is too long to read: it holds what a point is, each record and each distance. A town centre or a ward is named by an id alone. "Other names" is not after "Size". "No receipt" says "or" |
| Names, `j` from the first name | It passes the fourth name, which carries a mark to settle and no other flag. "Here because" does not say that the draft has a mark on it to settle |
| Names, the 23rd name, which is the first proposed as another name | An answer with the key `1` is shown. The answers do not begin at `2`. The line that says why there is no key `1` is not over the answers, or pushes the note or the mark out of view. A click on an answer gives another answer than the one clicked |
| Borders, the first border, as it opens | A code is printed on a cell that is not under the cross. A mark is not told from another: the ring, the square, the square on its point and the triangle. On a cell under two doubts one mark hides the other. The words in the top left corner lie over a cell that matters, or are not read against the colours of the cells |
| The same border: an arrow until the cross is on a mark, then `+` twice | The code of the cell under the cross is not shown, or is far from its mark. Twice as close, a mark in view has no code, or codes lie over each other |
| Borders, the second border, which is flagged for following no line | No heavy dotted line runs along the border. It runs along a ward line or a main road. It is taken for a road, or for the outline of the area. It is drawn inside the area |
| Borders, the fourth, which is flagged for two town centres | A town centre the flag names is not named in heavy letters, or its name lies under the cross. A name lies over the words in the corner |
| Borders, the tenth, which is flagged for a seed close to another | The other seed has no two rings round it. No broken line joins the two seeds. The line is taken for a border. The rings hide the name of the seed |
| Any border with cells in doubt: the first line and the line "In doubt" | The first line counts cells in doubt. The line "In doubt" is too long to read at a glance. A line of a cell says "margin" with a number of a hundred or more |
| The same screens at 1280 by 720, and in dark | A line added here pushes an answer, the note or the mark out of view. A mark or the dotted line is not seen against a dark cell |

**Still wrong, and left.**

| Where | What |
|---|---|
| Rules | The upper part of the column is empty while a rule is read. `o` has no button: it is a key alone. A rule is read from its top again when `o` comes back to it |
| Rules | "Would settle" on the fifth rule says 40, which is what it would settle with all four rules adopted. What it would settle as the rules stand is on the line "As the rules stand" |
| Names | 92 names have no point on the map. For 91 the town centre of the name is drawn and named. One has neither: its record lies outside its area, as its line says |
| Names | A name is said to rest on a source by the id of the source, and not in words |
| Borders | The name of a seed is at times moved so far that it reads as the name of the next place |
| Borders | "No receipt" on a border still says "its name or its seed", and not which |
| Whole boroughs | Nothing is marked on the map of a whole borough: the marks are of a border |
| The column | At 1440 by 900 what is known of a name takes one `.` to read to its end, and on the first name of a sitting three lines of it are in view while what to do is open. The lines of a name are longer now than they were |
| The top line | At 1280 by 720 the progress beside it may wrap to a second line |

## 14. What the founder decided, and what the desk does with it, 2026-09-24

The founder decided two things that touch the desk. Each change is held by a test. The draft of London was made again from the fetched files, the desk was filled from it and asked over its own port, and no browser was open. Every count is over all of London and names no place. The ground of the draft did not change: every output area is in the area it was in. Nothing of the draft is in the repository.

| Decided | What the desk does | Held by |
|---|---|---|
| One official publisher is enough for a name: [ADR 0022](../adr/0022-one-official-publisher-is-enough-for-a-name.md) | It makes no item of the name of an area whose row of `areas.csv` says `named_by_rule`. It asks about the border of that area as before. When it has filled its queues it says how many names stand, and the time they would have taken | `test_a_name_that_stands_by_the_rule_is_no_item_and_its_border_is_one`, `test_the_run_says_how_many_names_stand_and_are_not_asked_about` |
| | A name the draft flags is asked about whatever its row says, and so is a name that the desk's own list of words finds may say who lives there | `test_a_name_the_draft_flags_is_asked_about_whatever_its_state`, `test_a_name_that_may_say_who_lives_there_is_put_to_the_founder_whatever_the_draft_says` |
| | A line or a rule of a name that stands stops the fill: the draft and the desk would disagree about what is asked | `test_what_a_draft_says_of_a_name_that_stands_stops_the_fill`, `test_a_rule_that_names_a_name_that_stands_stops_the_fill` |
| | `compile` knows the state `named_by_rule`, below `name_checked`: nobody read the name. A border called right raises it as it raises any other | `test_a_name_that_stands_by_a_rule_is_below_one_a_person_has_read` |
| | Each rule says what is decided already, under what it would settle. A rule with nothing left to settle is still shown, and draws no item | `test_a_rule_with_nothing_left_to_settle_is_shown_and_draws_no_item` |
| | The border of an area whose name stands says first that nobody has read the name, what the name stands on, and what to do if it looks wrong. The draft says it, in `lines.csv` | In the areas build, `test_the_border_of_an_area_whose_name_nobody_read_says_so` |
| | The flag for one publisher says in its words that one is not enough for the name. It says nothing of where a record lies: the flag is raised on a wide name too, and the made-up city plants it on a name whose record lies inside. The line "Publishers" of the item says why one is not enough | In the areas build, `test_the_words_of_the_flag_say_that_one_publisher_is_not_enough_and_not_where_it_writes`. At the desk, `test_the_words_of_the_flag_for_one_publisher_are_true_of_every_name_it_is_planted_on` |
| The second copy of every decision is kept in a folder in the home folder | Section 3, "The kept copy" | `test_real_data_is_served_with_its_second_copy_in_a_folder_of_the_home_folder`, `test_real_data_is_not_served_where_the_home_folder_holds_no_such_folder` |

**What each queue holds.** At the pace of section 1, which nobody has timed.

| Queue | Items before | Hours before | Items now | Hours now | Flagged now |
|---|---|---|---|---|---|
| `rules` | 8 | 0.3 | 8 | 0.3 | 0 |
| `know` | 33 | 0.05 | 33 | 0.05 | 0 |
| `names` | 783 | 9.8 | 421 | 5.3 | 267. It was 674 |
| `borders` | 488 | 65.1 | 488 | 65.1 | 279 |
| `whole` | 33 | 8.2 | 33 | 8.2 | 33 |
| **All five** | **1,345** | **83.4** | **983** | **78.9** | |
| `borders`, the flagged alone | 279 | 37.2 | 279 | 37.2 | |

| Counted on the draft | Before | Now |
|---|---|---|
| Names of areas that stand, and are not asked about | 0 | 362 of 488: 4.5 hours of names |
| Names of areas still asked about | 488 | 126: 101 that the rule fits and the draft has a mark on, and 25 that the rule does not fit |
| Other names asked about | 295 | 295. The decision is about the name of an area |
| Names flagged for one publisher | 613: 334 of areas, 279 others | 86: 8 of areas, 78 others |
| What the eight rules would settle | 438 names, 26 borders | 172 names, 26 borders |
| Names the first three rules fitted that stand already | | 240: 104, 120 and 16 |
| Names left, were every rule adopted | 345 | 249 |
| Lines the desk is handed of names | 5,140 | 2,770 |
| Borders that say nobody has read the name of the area | 0 | 362 |

**What a rule now says.** The first three rules each say how many names they fitted, that every one stands by the decision, and that nothing is left to settle. The second no longer says that it waits on the decision. The fifth leans on the fourth alone, and settles 21 other names where it settled 40 names. The 19 names of areas it once let through carry a mark, and a mark is a doubt the decision did not settle: each is read by a person.

**Look at these in a browser.** Each is a change to what is shown, made with no browser open.

| Look at | What would be wrong |
|---|---|
| Rules, the first rule | "Already decided" is not under "Would settle". It is too long to read at a glance. The page offers to open ten items, and there is none |
| The same rule: `1`, then `u`, then `2` | What was saved does not say that nothing was changed. The rule does not leave the queue |
| Rules, the fifth rule | "Leans on" names a rule other than the fourth. "As the rules stand" counts 40 |
| Names, as it opens | The top line does not count 421. Nothing says that 362 names stand and are not asked about: it is said when the queues are filled, and on each rule, and nowhere on the page of Names |
| Names, a name that one publisher writes | The line "Publishers" is not under the records. It does not say whether one is enough |
| Borders, the border of an area whose name stands | Its name is not over the item. The line "Name" is not the first thing read of it, or is cut short. It reads as a flag of the border |

**Still wrong, and left.**

| Where | What |
|---|---|
| Names | The page of Names does not say how many names stand by the rule. A person who opens Names first does not learn it there |
| Rules | A rule with nothing left to settle is still one of the eight, and is counted as left until it is answered |
| Names | A name that stands cannot be turned down at the desk, which holds no item of it. It is turned down by hand, in the file of decisions: areas section 19 |
