# The desk, in five minutes

The desk is where one person looks at what Burro serves, flags what looks wrong, and decides what it should say. It runs on your own machine and opens in your browser. It has two halves: **the panel**, which this page is about, and **the queues**, which [the design of the desk](design/desk.md) is about.

## Start it

| To open | Type | What it shows |
|---|---|---|
| The made-up city | `make desk` | The synthetic release. Nothing in it is a real place, so try anything |
| London | `make desk RELEASE=data/releases/ID` | The release in that folder, and what you decided before. What you decide is kept in `data/raw/desk` |

It prints `Open http://127.0.0.1:8765/`. Open that address in a browser on the same machine. `Ctrl-C` stops it. It listens on this machine and nowhere else. On London it keeps a second copy of every line in the folder `burro-desk-decisions` in your home folder, and does not start until that folder is there: `make desk KEEP=FOLDER` names another.

**From a clone and a release, and nothing else.** A release is its folder and the folder beside it, named for it with `-build` after.

| Step | Type | It prints |
|---|---|---|
| 1 | `make setup` | What `uv sync` installs, and then nothing: the check of the repository passes in silence |
| 2 | `mkdir ~/burro-desk-decisions` | Nothing. It is made once. Without it step 3 prints "The desk did not start. On real data the desk keeps a second copy of every decision", and how to make it |
| 3 | `make desk RELEASE=data/releases/ID` | "The review desk, as r1.", "REAL DATA FOR LONDON. A draft that nobody has checked. What you decide here is built.", where decisions are kept, where the second copy is kept, "The panel shows the release in data/releases/ID.", "No queue is filled, so the panel is all there is.", and `Open http://127.0.0.1:8765/` |
| 4 | Open the address | The panel. The queues are filled from a draft of the areas, which needs the publishers' files: [the design of the desk](design/desk.md) says how |

A release that breaks a rule is refused at step 3 in one line, which names the file and the rule: "The desk did not start. The release cannot be shown."

## The first screen

Three things, in this order: **what is served today**, which is the release, the day it was built, and how many areas, measures and vibes it holds. **What is waiting for a person**, which is each queue with how many items are left. **What was changed and not yet built**, which is every change you kept since the release was built.

## What each part is for

| Part | What you do there |
|---|---|
| Areas | Find an area by its name, its borough or on the map. Read every figure with its unit, its source, its date and the files it rests on. Read every vibe with its band and the share of each part. Read what the area has no figure for, and why |
| Measures | Read how a measure is spread, the areas highest and lowest, and the areas with no figure. Read what stands out: a figure far from the areas beside it, and a figure at nought where they are not. Give the measure another label |
| Vibes | See the five bands on the map, the areas highest and lowest, and how closely the vibe follows homes per hectare and the distance from the centre. Read the bands that rest on little of the recipe. Move the shares of the recipe. Give the vibe and its ends other names, and change what it says it cannot see |
| Brands | Move a chain to another tier, add a chain, take one out |
| Numbers | Read the numbers that were set by judgement. None is changed here yet |
| Flagged | The list of everything that is flagged, on one page |
| History | Every change, newest first: who, when, what stood before, what stands now, and why. Take any one back. See where two reviewers differ |
| The queues | Names, borders and the rest, one item at a time |

## To flag, and to change

**To flag** a figure, a band, a name or a border, press Flag beside it and say why. That is all. You never type a figure: a figure is the publisher's.

**To change** a recipe, a name, a label or the table of brands: make the change, press to look at it, read what would move, say why, and keep it. For a recipe the panel says how many areas change band, which rise and fall most, and the first ten areas of three searches before and after. Nothing is kept that you did not look at, and nothing is kept without a reason.

**To take a change back**, press Take back beside it in the History, and say why. Taking back is a line too, so nothing is ever rubbed out.

## How a change reaches what is served

1. What you keep is one line of a plain file, `decisions/changes/r1.jsonl` in the desk's folder. **Nothing that is served has changed.**
2. `make desk-publish ARGS="--data data/raw/desk --to gazetteer/london"` makes the copy that may be committed, and prints every reason for you to read first. Commit it.
3. `make preview ARGS="--release-id ID --built-at TIME --out data/releases --changes gazetteer/london/decisions/changes/r1.jsonl"` builds a release from it. A build takes the founder's file alone, and only as it was committed. With no `--changes`, a build is byte for byte what it was. A hosted build of London takes the same file once it is committed to `main`, with nothing for you to name: [the guide to data builds](data-builds.md), "London, from the bucket to the service".
4. The build stops at a line it cannot apply, and says its number. The release it writes carries what you decided, and its record lists each line it applied.
5. `uv run burro-release check data/releases/ID` says whether the release may be served. Open the panel on it, and the first screen says which of your lines it was built with.

## What the panel never does

| It never | Because |
|---|---|
| Lets you type in a figure, or fills in a missing one | Every figure traces to a file of its publisher |
| Ranks on ethnic group, religion or country of birth, or lets a recipe ask for fewer of anyone | Burro ranks places, and never residents |
| Holds a search of anyone's | The three searches of the preview are written in the repository. One is the founder's own test sentence |
| Changes what is served | A build is made on purpose |

[The design of the panel](design/panel.md) says how each of these is held, and what is not built yet.
