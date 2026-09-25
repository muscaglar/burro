# tools/desk

The review desk: where a person looks at data and decides. One small server on the person's own machine, one page, plain files. It is built to [docs/design/desk.md](../../docs/design/desk.md). If code and design disagree, change one of them in the same commit.

The desk has a panel: a second page, where a person looks through a release, flags what looks wrong, and renames or adjusts what is worked out. It is built to [docs/design/panel.md](../../docs/design/panel.md). Nothing a person does at the panel changes what is served: a change is a line of a file of changes, and a build that is given the file applies it.

Real files have been fetched since the desk was built, and its fill step and its server were run on a draft made from them: the design says where that is written up. The page has been opened in a browser twice, on 2026-09-24, by a program and not by a person: once on the made-up city, and once on the first draft of London. Section 10 of the design lists what to look at again on the made-up city, in order, and what nobody has yet seen. Section 12 says what the sitting on the draft of London read and what was mended. Section 13 says what was done about what that sitting left, with no browser open, what to look at in a browser, in order, and what is still wrong. The head of the design says in ten lines how to sit down at the draft of London.

## Commands

```
make desk                  start the desk and its panel on 127.0.0.1:8765, as r1, and print the address to open
make desk RELEASE=FOLDER DATA=FOLDER KEEP=FOLDER   the same on real data: the release the panel shows, the desk's folder of data, and where the second copy is kept
make desk RELEASE=FOLDER BEFORE=FOLDER   the same, with the release that is shown held against one other: the screen "What moved"
make desk KEEP=FOLDER      the same, with the second copy of every decision in a folder of your own, outside the repository
make desk REVIEWER=r2 ARGS="--port 8766"
make desk-check            the desk's tests, and the page's with node --test
make desk-take DRAFT=FOLDER   take a draft of the areas to the desk: copy what it hands the desk, and fill the queues
make desk-fill ARGS="--from data/raw/desk/draft --data data/raw/desk"
make desk-fill ARGS="--made-up"      fill the made-up city again, after the fill step changed
make desk-compile          make a build's files from the decisions. For London: ARGS="--data data/raw/desk --gazetteer gazetteer/london"
make desk-publish ARGS="--to gazetteer/london"   make the copy of the decisions that may be committed, and print its notes
```

`make desk` needs `uv` and Python 3.13. Its queues need no package: `PYTHONPATH=tools python3 -m desk serve` starts them alone. Its panel reads a release with core and the pipeline, so `make desk` is run after `make setup`, and where the packages are not there the desk serves the queues and says so. It serves `data/raw/desk` if that holds items, and then keeps a second copy of every decision in the folder `burro-desk-decisions` in the home folder, or in the folder `KEEP` names. It does not serve real data where neither is there, and makes no folder by itself. If `data/raw/desk` holds no items, it serves the made-up city from `data/raw/desk-synthetic`, and fills it the first time. The panel shows the release `RELEASE` names. With none named, the made-up city is shown the committed synthetic release, and real data is shown none. It needs a Mac or Linux.

## The parts

| Files | What they do |
|---|---|
| `records.py` | The line of a decision, the file it is kept in, which line stands, and progress. It reads no clock but to stamp a line |
| `server.py` | The routes of section 4, and every refusal |
| `compile.py` | Makes a build's files from the lines, and the list of what a person flagged. A pure step |
| `publish.py` | Makes the copy of the decisions that may be committed, and of each file of changes. A pure step |
| `cli.py`, `__main__.py` | The four commands |
| `fill/`, `questions.json` | Fills the queues from a draft folder, or from the synthetic release. The twelve questions, in the order of the work |
| `page/` | The page of the queues, and the page of the panel. Its own `README.md` has the keys |
| `panel/look.py` | What the panel shows of a release: an area, a measure, a vibe, and what stands out. It reads a release as it is served, and writes nothing |
| `panel/kept.py` | The file of changes on the disk: `decisions/changes/<reviewer>.jsonl`. `burro_pipeline.changes` says what a line holds, and is the one reader of it |
| `panel/preview.py`, `panel/searches.json` | What a change would move, worked out by core before it is kept: the bands of a vibe, and the first ten areas of three searches. A search is ranked by `burro_pipeline.upkeep.searches`, which the step `moved` ranks it by too |
| `panel/numbers.py` | The numbers set by judgement, read from core and listed. None is changed here |
| `panel/routes.py` | What each route of the panel answers, and every refusal of it |

## Rules

- **Standard library only, but for the panel.** `fill/gate.py` alone imports the pipeline, and only for real files. `panel/` imports core and the pipeline, to read a release as it is served and to work a band out as a build does, and nothing else of the desk imports `panel/` but `cli.py`, by name and only when the desk starts. No package is added for either.
- **The panel takes no figure.** A figure is a publisher's. A route of the panel takes an id, a reason and what a person may adjust, and a field it does not know is refused. A line of the file of changes holds no figure of a place: a flag names its figure by the area and the measure.
- **A name a person gives is held to the rule of a name before it is kept.** The name of a vibe, of an end of one, a line of what a vibe cannot see and a label of a measure each go through `what_a_vibe_breaks()` or `what_a_measure_breaks()` in core, by way of the reader a build uses. A measure that counts who lived somewhere keeps the name core gives it. Do not check a name in the page or in a route of the panel: one rule, in one place.
- **The panel opens on a release alone.** `make desk RELEASE=FOLDER` needs no queue filled: a desk with no item is of the city of the release its panel shows, and keeps what is decided where that city's decisions are kept. With no release and no item there is nothing to show, and the desk says so. Nothing of London is ever kept in the folder of the made-up city because no folder was named.
- **The panel's limits protect nothing: the file can be written by hand.** What protects what is served is what the reader, the build and core refuse ([the design](../../docs/design/panel.md), section 9). So a limit is never written in the page or in a route alone. The panel asks the reader a build uses, and core's own rules, and refuses what they refuse.
- **Nothing is kept that a build would stop at.** The file has a line for a figure that is left out, and no build applies one yet. So the route of a flag refuses it, and the page does not offer it.
- **Nothing is kept that was not looked at.** `POST /api/panel/keep` takes the mark of the preview of that very change, and works the change out again before it writes. What the page worked out is never trusted: a recipe is held to `checked_recipe()`, by the reader a build uses.
- **No route adds a part to a recipe, takes one out or turns one round.** A slider is of a part the recipe holds. So no slider can take a census figure that a recipe does not hold already, and none can read one from its low end.
- **What moved between two builds is the pipeline's to work out.** `routes.moved_since` hands two releases to `burro_pipeline.upkeep.moved.compare`, once, as the desk starts, and the screen draws what it found. Do not compare two releases in the page or in a route: the step `moved` and the screen must say the same. The screen has no press: a build is approved by committing its lock, and never at the panel.
- **The release that is shown is read as it is served, and the one it is held against by its own catalogue.** `routes.held_against` opens the other release as the step `moved` does, whatever the version of its catalogue, and it is handed to `compare` and to nothing else. Do not open the release that is shown that way, and show no figure of the other as served: a build of another catalogue may hold what core no longer does.
- **The panel holds nobody's search.** The searches of the preview are typed edits in `panel/searches.json`. The founder's own sentence is read from the evaluation set, and a place is named by where its words stand in the sentence, never by the words.
- **The panel shows no census table and no household income**, and `panel/` imports neither module of core. A test reads the imports.
- **A line of the file of changes is written as it may be committed.** It says the day and never the hour, and the reviewer by a label. The reason is a person's own words: it is never printed, and a refusal never repeats it.
- **A line is never changed and never removed.** Undo is a new line. `append` is the only function that writes a line, and it returns once the line is on the disk.
- **Lines are put in order by `n`, never by `at`.** A clock that goes backwards must change no answer.
- **The server writes only under `<data>/decisions/` and `<data>/decisions-private/`**, and under the kept copy where one is named. It builds no path from the words of a request. A new route takes its words as keys of a table made at start. The files of changes lie among the decisions, in `decisions/changes/`, so that the kept copy holds them too. No queue may be named `changes`.
- **A line that may never be published is kept apart.** A queue whose question says `public: false` writes to `decisions-private/`, and what `compile` makes from it goes to `out/private/`, which only its owner may read. `publish` reads the public tree alone. A new queue must say which it is.
- **What is published says the day and never the hour**, and leaves out the time on screen.
- **A file of changes is published whole, byte for byte**, because the lock of a build names it by its hash. So a line of one is written as it may be published: the day, a reviewer's label, no figure. Every reason in it is handed back to be read before it is committed, as a note is. `tools/tests/test_published_words.py` reads a published decision as a document, and `tests/test_panel_tracked.py` holds where one may be.
- **Nothing is trusted between runs.** `records.Files` holds what a file held while its size, its time of change and its place on the disk stand. Read a file of decisions through it, and write through it, or a request pays for the whole file again.
- **Every answer under `/api/` carries `synthetic`**, errors included. A layer carries it under `desk`.
- **A refusal is fixed text.** It never repeats what was sent. The log holds the method, the route's template and the status.
- **An address is read by its path.** `route` cuts it at the first question mark, and nothing reads what follows. Do not take a word of a request from there.
- **The reviewer is a label**, `r1` to `r99`, named when the server starts. A build's files hold a role: `founder` or `reviewer-2`.
- **Rule 8.** An item has the eleven keys of section 8 and no other, and `read_items` refuses any more. Nothing about who lives somewhere is shown beside a name, a border or a vibe.
- **Rule 3.** No basemap, no tiles, no request to another host. The content security policy makes the browser refuse one.
- **The made-up city and London are never mixed**: not in a folder of items, not in a file of lines, not in a gazetteer. The made-up city is filled only into a folder whose name ends `-synthetic`. `compile` writes it under `<data>/gazetteer` and nowhere else, and every row under `out/` says whether it is made up. `publish` refuses it.
- **`compile` applies a decision whole or not at all.** What it cannot apply it lists in `not_applied.csv`, with one of the reasons below, and the draft stands. It fails, and writes nothing, only where the files would break: a cell with no area, a reviewer with no role, a line of the other city.
- **A name that stands by a rule the founder has decided is no item.** The draft says `named_by_rule` of its area in `areas.csv`, and `fill/draft.py` makes no item of the name. It makes one all the same where the name carries a flag, the desk's own flag for a name that may say who lives there among them. A line or a rule of a name that is no item stops the fill. `compile` leaves the state as the draft wrote it, below `name_checked`: nobody read the name.
- **The code holds no path.** The folder of the second copy is a name, `KEPT_IN_HOME`, looked for in the home folder of whoever starts the desk. Write no path of any machine in the desk, and none in the head of the design.
- **The desk adopts no rule.** A draft puts rules, and only the founder's yes in the queue `rules` adopts one. `server._settle` then writes a line for each item the rule fits that the founder has not answered, and names the rule in its `detail`. It never writes over a person's answer, and it takes back what a rule wrote only by a line of its own. A request may neither give the answer `rule` nor name a rule in a `detail`.
- **A rule that leans on another settles only what the other, once adopted, would settle.** An item says in `preset.leans_on` which rule it leans on. `server._settle_queue` settles it only where both rules are adopted, and takes it back when either is no longer. A new rule that lets an item through to another rule names that rule in the draft, or it settles on its own say-so.
- **What a rule settled is never counted as read.** `records.by_rule` says whether a line is a rule's. Such a line is left out of the pace, of what `u` takes back and of where the desk opens again, and is counted apart in the counts, on the top line and by `compile`.
- **An answer that waits is said at once.** The desk cannot take the ground from under an area. The item says what its area holds, in `preset.holds`, and the page says before the answer is given that a build will set it aside. `compile` keeps the row of a name that was turned down in `out/names.csv` once the draft is made again without it, so that the next draft leaves it out too.
- **A draft's doubt is never lost without a word.** The fill reads `lines.csv` and `marks.csv`, and refuses a line or a mark of an item it does not make, a flag with no words, and a rule that fits an item the queue does not hold.
- **How many cells are in doubt is the draft's to say.** The desk counts the cells of a border and those on a border, and no cell in doubt: two counts once stood side by side and differed.
- **No flag of a person's is read by nothing.** Every answer is written with its note and its mark. What was called wrong, was not known, was marked, or was skipped with a note is in `out/private/to_look_at.csv`. A new answer that decides nothing belongs in `records.NOT_KNOWN` or `records.CALLED_WRONG`.

## What the server adds to the design

The page may rely on these. Section 4 of the design names the rest.

| Where | What |
|---|---|
| `POST /api/decide` | A decision made twice is written once: the same answer to the same item gives back the line that stands, whatever `stands` says. `seconds` over 900 is cut to 900 |
| `POST /api/decide` | `wrong` needs a note, and so does an answer on an item that has a move. `settles` is taken only from `r1`, and only on an item in dispute. Each is `bad_request`, with its own words |
| `POST /api/decide`, `POST /api/undo` | In `rules`, the answer holds `ruled`: how many items were settled, how many answers of a rule were taken back, and as `held_back` how many wait on a rule that is leant on and not adopted. Each of those lines is on the disk, and in the kept copy, before the desk answers |
| `GET /api/state` | The counts of a queue hold `by_rule` and `set_aside`. A row of `waits` holds `set_aside` where an answer in that queue waits for a new draft, and is then listed though nothing is left to read |
| `GET /api/queue/...` | Each item says whether it is `flagged`, for the key that goes to the next flagged item |
| `GET /api/item/...` | For a stale item `mine` is the old line, so that it can be shown |
| `GET /api/item/rules/...` | `leans` says how each rule stands that the rule leans on, and how many of its items lean on each |
| Any route | `405` for any method but `GET` and `POST`, and for a route asked with the wrong one |
| `GET /` | Asked by a browser that opens it as a page from another site, it is refused with `403` and a small page of fixed words in place of JSON, which holds a link to `/`. `server.ELSEWHERE` holds the words. No other request is given it |
| `GET /` | Where the desk holds a panel it is the page of the panel, and the page of the queues is `/page/index.html`. Where it holds none it is the page of the queues, as before |
| `/api/panel/...` | The routes of the panel: [the design of the panel](../../docs/design/panel.md), section 7. With no panel each is `404`, with `server.NO_PANEL` as its words |

## How two reviewers meet, by queue

| Queues | Rule |
|---|---|
| `names` | The founder alone. Another reviewer's lines are kept and never applied |
| `borders`, `whole`, `claims`, `sentences` | Answers that differ are a dispute. Nothing is applied until `r1` writes a line that settles. An answer that does not know is left out where another reviewer decided. Only `r1` and `r2` have a role |
| Every other queue | Each reviewer's answer is a row of its own. A rating is never in dispute |

## Why a decision was not applied

| `why` | Means |
|---|---|
| `no_note` | A move on an item that has no answer with a note. The note is the reason a build writes |
| `disputed` | The reviewers differ on the item, or the founder settled it another way |
| `moved_to_two_areas` | One cell was moved to two areas, in `borders` and in `whole`, or by two reviewers |
| `item_changed` | The item was filled again since the move was made |
| `no_area_named` | A name was called another name of an area, and the line names no area. The page asks for one before it sends such an answer |
| `no_area_id` | Another name was called an area. Only the areas build gives an area its id. The desk refuses such an answer, so this is of a file that did not come through it |
| `no_such_area` | A name was given to an area that is not in the files |
| `not_a_spelling` | The spelling chosen is not one a source wrote |
| `area_has_cells` | A name was turned down while cells are drafted to it. The page said so before the answer was given. Make the draft again from `out/names.csv`, and fill the queues again |
| `area_has_names` | A name was dropped while another name is still given to it. Decide that name first |

## Testing

- Tests are named for what they protect, and every name, id and note in them is made up.
- `tests/test_server.py` asks the server through its own port, under `pytest.mark.allow_hosts(["127.0.0.1"])`. One test starts the desk as `make desk` does, on the real page and the real fill. `tests/test_cli.py` and `tests/test_publish.py` run the commands with no socket.
- `tests/test_rules.py` adopts the made-up rules of the synthetic release through the desk's own port, and reads the build's files and the copy that may be committed.
- Two tests hold the three parts together, and both fill the queues from the synthetic release. `tests/test_walk.py` makes every request the page makes, for ten items of each queue, with the desk stopped and started in the middle, and then reads the build's files. It says no to every rule, so that every other line is a person's. `tests/test_page_at_the_desk.py` runs the page's own code against the server, with a stand-in for the browser. It needs Node, and is left out where there is none.
- After a change to a route, a field, an item or a key, run both. If one fails, the parts no longer fit: mend the part, not the test.
- A test of a refusal uses the fixture `refusing`: one server for them all, which fails at the end if any of them wrote a line.
- No test opens a browser. How the page looks, and how it feels to the hands, is for a person to check.
- What moved is held by `tests/test_panel_moved.py`, which asks the panel with no port, on the made-up city held against itself with one figure lower and one measure gone, and held against itself as a build of the catalogue before. Its last test hands what the desk answers to the page's own code, with no port and no browser.
- The panel has four tests of its own. `tests/test_panel_look.py` reads the committed synthetic release with no port. `tests/test_panel_server.py` asks the panel through the desk's own port. `tests/test_panel_at_the_desk.py` runs the panel's own page against the desk, with a stand-in for the browser. `page/test/panel.test.mjs` holds the page's files and every screen. No browser has opened the panel.
- A test of the page never compares two elements of the stand-in by value. When such a test fails, the runner prints both, and an element holds the whole page: the run does not end.
- After a change here, run `make desk-check`, then start the desk and answer an item.
- The desk's tests take about 14 seconds, and the page's under one. The root `AGENTS.md` says what the whole of `make ci` takes.
