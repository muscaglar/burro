# tools/desk

The review desk: where a person looks at data and decides. One small server on the person's own machine, one page, plain files. It is built to [docs/design/desk.md](../../docs/design/desk.md). If code and design disagree, change one of them in the same commit.

Real files have been fetched since the desk was built, and its fill step and its server were run on a draft made from them: the design says where that is written up. The page has been opened in a browser twice, on 2026-09-24, by a program and not by a person: once on the made-up city, and once on the first draft of London. Section 10 of the design lists what to look at again on the made-up city, in order, and what nobody has yet seen. Section 12 says what the sitting on the draft of London read and what was mended. Section 13 says what was done about what that sitting left, with no browser open, what to look at in a browser, in order, and what is still wrong. The head of the design says in ten lines how to sit down at the draft of London.

## Commands

```
make desk                  start the desk on 127.0.0.1:8765, as r1, and print the address to open
make desk KEEP=FOLDER      the same, with the second copy of every decision in a folder of your own, outside the repository
make desk REVIEWER=r2 ARGS="--port 8766"
make desk-check            the desk's tests, and the page's with node --test
make desk-take DRAFT=FOLDER   take a draft of the areas to the desk: copy what it hands the desk, and fill the queues
make desk-fill ARGS="--from data/raw/desk/draft --data data/raw/desk"
make desk-fill ARGS="--made-up"      fill the made-up city again, after the fill step changed
make desk-compile          make a build's files from the decisions. For London: ARGS="--data data/raw/desk --gazetteer gazetteer/london"
make desk-publish ARGS="--to gazetteer/london"   make the copy of the decisions that may be committed, and print its notes
```

`make desk` needs `uv` and Python 3.13, and no package. It serves `data/raw/desk` if that holds items, and then keeps a second copy of every decision in the folder `burro-desk-decisions` in the home folder, or in the folder `KEEP` names. It does not serve real data where neither is there, and makes no folder by itself. If `data/raw/desk` holds no items, it serves the made-up city from `data/raw/desk-synthetic`, and fills it the first time. It needs a Mac or Linux.

## The parts

| Files | What they do |
|---|---|
| `records.py` | The line of a decision, the file it is kept in, which line stands, and progress. It reads no clock but to stamp a line |
| `server.py` | The routes of section 4, and every refusal |
| `compile.py` | Makes a build's files from the lines, and the list of what a person flagged. A pure step |
| `publish.py` | Makes the copy of the decisions that may be committed. A pure step |
| `cli.py`, `__main__.py` | The four commands |
| `fill/`, `questions.json` | Fills the queues from a draft folder, or from the synthetic release. The twelve questions, in the order of the work |
| `page/` | The page. Its own `README.md` has the keys |

## Rules

- **Standard library only.** `fill/gate.py` alone imports the pipeline, and only for real files.
- **A line is never changed and never removed.** Undo is a new line. `append` is the only function that writes a line, and it returns once the line is on the disk.
- **Lines are put in order by `n`, never by `at`.** A clock that goes backwards must change no answer.
- **The server writes only under `<data>/decisions/` and `<data>/decisions-private/`**, and under the kept copy where one is named. It builds no path from the words of a request. A new route takes its words as keys of a table made at start.
- **A line that may never be published is kept apart.** A queue whose question says `public: false` writes to `decisions-private/`, and what `compile` makes from it goes to `out/private/`, which only its owner may read. `publish` reads the public tree alone. A new queue must say which it is.
- **What is published says the day and never the hour**, and leaves out the time on screen.
- **Nothing is trusted between runs.** `records.Files` holds what a file held while its size, its time of change and its place on the disk stand. Read a file of decisions through it, and write through it, or a request pays for the whole file again.
- **Every answer under `/api/` carries `synthetic`**, errors included. A layer carries it under `desk`.
- **A refusal is fixed text.** It never repeats what was sent. The log holds the method, the route's template and the status.
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
- A test of the page never compares two elements of the stand-in by value. When such a test fails, the runner prints both, and an element holds the whole page: the run does not end.
- After a change here, run `make desk-check`, then start the desk and answer an item.
- The desk's tests take about 14 seconds, and the page's under one. The root `AGENTS.md` says what the whole of `make ci` takes.
