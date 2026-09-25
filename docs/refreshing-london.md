# Refreshing London: from what is due to what is served

For the founder. Written 2026-09-25. It puts in one order what [the guide to data builds](data-builds.md) and [the guide to deployment](../deploy/README.md) say at length, and adds the step at each end of it: `fresh`, which says what is due, and `moved`, which says what a build changed.

**A hosted run fetched on 2026-09-24, and one built London whole on 2026-09-25. The API and the website are deployed, each with the made-up city: no release of London is approved, taken or served.** The two steps added here were driven on the receipts this repository holds, and on two builds of London made outside a hosted run, of two versions of the catalogue. Every hosted step below is as its own guide gives it.

## 0. In short

| # | Do this | With | It takes of you |
|---|---|---|---|
| 1 | See what is due | `fresh`, on a machine of your own | 2 minutes |
| 2 | Bring forward each list that pins an edition | An editor, then `plan` and `make ci` | Not known: you read each publisher's page |
| 3 | Fetch | The hosted run `data-fetch`, and `by-hand` for four files | 5 minutes a list, and a browser for the four |
| 4 | Bring the receipts back, and commit them | `receipts`, on a machine of your own | 5 minutes |
| 5 | Build | The hosted run `data-london` | 5 minutes, and two approvals |
| 6 | See what moved | `take`, then `moved` or the panel | 15 minutes to read |
| 7 | Approve | Commit the lock | 5 minutes |
| 8 | Deploy | `take`, then `fly deploy` with `--depot=false` | 15 minutes |

Each step is a section below, under its number. Steps 2, 4 and 7 each end in a commit that must be on `main` before the step after it: a hosted run reads `main`. So a refresh is **three pushes**, or two where no list pins a file that is refreshed.

## 1. See what is due

```
uv run python -m burro_pipeline fresh --on 2026-09-25 --table
```

Give the day that is today: the step reads no clock. It reads the registry, the lists and the receipts, and asks nothing of a publisher. It prints a row for each file that has a receipt, what is due first, and then one line:

```
step=fresh status=ok on=2026-09-25 receipts=88 due=0 fresh=87 not_known=1 older=0 unlisted=0 not_said=1
```

| The row says | It means |
|---|---|
| `due` | The file was retrieved longer ago than its publisher's rhythm: over 7, 31, 92 or 366 days. **It is time to look at the publisher's page.** It does not say that a newer file is out |
| `fresh` | It was retrieved within the rhythm, or its publisher changes it rarely |
| `not known` | The registry does not say how often it changes, in words the step reads. The step names the source in a note under the table. Begin its `cadence` with a word of [the registry's table](../registry/README.md#how-a-cadence-is-read) |
| Bring forward: `nothing` | A fetch takes whatever the publisher gives today. Go to step 3 |
| Bring forward: `edition and data_period`, or `data_period` | The list pins them. Do step 2 first, or the fetch brings the file you hold again |

On 2026-09-25 every file was two days old or less, so none is due. One is not known: `tfl-step-free-station-topology`, whose publisher states no rhythm. The same receipts, read on later days:

| Read on | Due | What has come due |
|---|---|---|
| 2026-10-02 | 44 | What changes weekly or daily: the food register, the stops, the schools, the health reports, the planning data, and Transport for London's files |
| 2026-10-26 | 53 | And the monthly: prices, rents, the places, recorded crime, school inspections |
| 2026-12-26 | 62 | And the quarterly: Ordnance Survey's files, the postcode directory, the pharmacies, median prices |
| 2027-09-27 | 69 | And the yearly: the air, council tax, household income, and the traffic counts, which were fetched a day after the rest |
| Never, by age | 18 | What changes rarely: the census and its boundaries, deprivation, land use, outdoor space, the centres |

## 2. Bring a list forward

Of the 88 files, 40 state their own edition and need nothing. **45 have their edition and their period written in a list, and 3 their period alone.** A fetch writes what the list states on whatever arrives, so change the list first.

1. Open the publisher's page, which the item of the list gives as `page`. Find the newest file, its address, its edition and the period its data describes.
2. In `packages/pipeline/src/burro_pipeline/fetch/lists/NAME.toml`, change `url`, `edition`, `data_period` and `what` of the item. Where the entry of the source names the address whole under `file_urls`, change it there too, in `registry/sources/`: a file is fetched from no address its entry does not name.
3. Run `uv run python -m burro_pipeline plan --list NAME --words`. It must end `step=plan status=ok files=N ready=N`.
4. Run `make ci`. A test that holds the list to what it said fails, and names what to put right.
5. Commit, and bring it into `main`.

The receipt of the older file stays in `data/receipts/`. `fresh` then counts it as `unlisted`: no build takes it, and nothing is lost.

The Department for Transport's file of the flow at each count point is replaced once a year under one address, when a year of estimates is added to it. Its list, `m13-road-traffic`, pins the years it covers and no edition: bring the last year forward, in the list and in the test that holds the file to its page, and fetch. It is one file, of Great Britain, and the one more file a refresh of London fetches since the traffic near homes became a measure.

Transport for London's timetables are replaced each week under one address. Read the next issue with `describe --inside` before the list states its edition: [the guide to data builds](data-builds.md), section 7.

## 3. Fetch, by a hosted run

Open **Actions**, choose **data-fetch**, press **Run workflow**, choose the list, and approve the run in the environment `data-fetch`. It prints a line for each file:

| The line reads | It means |
|---|---|
| `status=ok new=1` | A new file arrived, and has its receipt |
| `status=ok new=0` | The publisher gave the file you hold. Its receipt stands as it was, **so `fresh` will call it due again tomorrow** |
| `status=refused why=18` | The address is not one the registry entry names. Item 2 of step 2 was missed |
| Any other | [The guide to data builds](data-builds.md), section 9 |

Four files are saved by a person, because their publisher gives them from a form: `naptan-london`, `gias-establishments`, `police-crime-london` and `postcode-directory`. Save each in a browser, and hand it over with the step `by-hand`, on a machine that holds the fetch key: `uv run python -m burro_pipeline by-hand --help` says how.

## 4. Bring the receipts back

A hosted run writes a receipt on a machine that is thrown away, and keeps a copy in the store. Bring the copies back, on a machine that holds the reading key, and commit them:

```
uv run python -m burro_pipeline receipts
git add data/receipts
```

It ends `step=store status=ok receipts=... new=...`. Bring the commit into `main`: a build checks its release against the receipts that are committed.

## 5. Build, by a hosted run

Open **Actions**, choose **data-london**, press **Run workflow**, and type the id of the release, as `lon-2026-10-02-01`, and the time it is said to be built. Approve the first build, and then the second. The run builds London twice, keeps the release where the two are the same byte for byte, and shows its lock at the foot of its summary page. [The guide to data builds](data-builds.md), under "London, from the bucket to the service", says what each step prints.

A green run ends `step=keep status=ok release=lon-2026-10-02-01 files=21 ...`. The release is then kept, and served nowhere.

## 6. See what moved

Take both releases to a machine of your own, with the take key, as step 8 gives it to a step: the one that is served, by its committed lock, and the new one, by a copy of its lock that is saved in any folder outside the repository.

```
uv run python -m burro_pipeline take --release lon-2026-09-25-01 --out data/releases/before
uv run python -m burro_pipeline take --release lon-2026-10-02-01 --approved FOLDER --out data/releases/look
uv run python -m burro_pipeline moved data/releases/before/lon-2026-09-25-01 data/releases/look/lon-2026-10-02-01 --out data/releases/moved
```

**The first time, no release is served, so the new one is held against nothing:** take it alone, read its lock and its coverage report, and run `moved` from the second release on. Where a build of London is kept on a machine of your own, the first release may be held against that, by the folder it was built to.

**The two builds need not be of one catalogue.** `moved` reads each by its own, so it says what moved after a measure or a vibe was added or a recipe was changed, which is when it is most needed. It refuses only a release it cannot read, and says the rule in words: one of a catalogue that is newer than the code the step is run from, one that does not hold together, and one that was changed since it was built. So run it from a working copy that is as new as the newer build.

`moved` prints counts, and ends with one line for the whole:

```
step=moved feature=highstreet_conserved came=1
step=moved vibe=village_feel areas=1002 changed=0 up=0 down=0 gained=925 lost=0
step=moved vibe=village_feel parts_came=2 parts_went=3 shares_changed=2 names_changed=0 rough_came=1 rough_went=0
step=moved search=1 kept=10 came=0 went=0 reordered=0
step=moved search=2 kept=10 came=0 went=0 reordered=0
step=moved search=3 kept=4 came=6 went=6 reordered=3
step=moved status=ok before=lon-2026-09-25-73 after=lon-2026-09-25-82 catalogue_before=13 catalogue_after=14 areas=1002 areas_came=0 areas_went=0 areas_renamed=0 areas_redrawn=0 measures=100 measures_came=1 measures_went=0 measures_moved=0 vibes=14 vibes_came=0 vibes_went=0 vibes_moved=1 costs_moved=0 files_changed=0 files_came=0 files_went=0 searches=3 searches_moved=1 parts_came=2 parts_went=3 shares_changed=2 names_changed=0 rough_came=1 rough_went=0
```

Those are the lines of two builds of 2026-09-25, one of catalogue version 13 and one of version 14. They say that one measure came, that Village feel gained a band in 925 areas and lost none, that its recipe gained two parts, lost three and holds two at other shares, that it became a rough guide, and that the third search, which asks for Village feel, has other areas among its first ten. No figure of any measure that both builds carry moved, and no file behind the builds is another file.

Then read `data/releases/moved/moved.md`, which says each part of a recipe that came or went by its name, and names the areas that moved most, or see the same at the panel:

```
make desk RELEASE=data/releases/look/lon-2026-10-02-01 BEFORE=data/releases/before/lon-2026-09-25-01
```

and open the screen **What moved**. The release the panel shows is the newer build, which the code serves, and the older is the one it is held against: the panel shows no release of another catalogue than its own. What is written names areas and gives figures of them: never commit it, and remove the three folders when you have read it.

| Read | For |
|---|---|
| `catalogue_before`, `catalogue_after` | The version of the catalogue each build was made under. Where the two differ, read the part of `moved.md` on the catalogue first: it is why the rest moved |
| `parts_came`, `parts_went`, `shares_changed` | A recipe that is made of other parts, or of the same parts at other shares. Every band of that vibe may move with it |
| `names_changed` | A measure or a vibe that people will find under another name. What is printed counts it, and `moved.md` says what the name was and is |
| `rough_came`, `rough_went` | A vibe that became a rough guide, or ceased to be one. A rough guide says so wherever it is shown, and is on a result only where it was asked for |
| A vibe with many `gained` | A vibe that places areas it did not place. With `changed=0` no area that had a band has another |
| `measures_went`, `vibes_went` | A measure or a vibe that people will no longer find. The lock names the rule that left it out |
| `areas_came`, `areas_went`, `areas_renamed`, `areas_redrawn` | Each should be nought unless the names or the borders were meant to change |
| A measure with many `lost` | A publisher's file that no longer covers what it did |
| `files_changed` | That every file you meant to refresh is another file, and no other |
| `searches_moved` | The first ten of each search, side by side. It is the nearest thing to what a person will see. A search is ranked on each build by what that build holds: where it asks for a vibe that one build does not place, `moved.md` says of which build, and the search is ranked without it there |

## 7. Approve, and 8. Deploy

| To | Do this | Where it is said in full |
|---|---|---|
| Approve | Save the lock the run showed as `data/approved/lon-2026-10-02-01.json`. Run `uv run --no-project python tools/release_lock.py read` on it, and hold its `sha256` to the run's. Run `make ci`. Commit the file and nothing else, and bring it into `main` | [Data builds](data-builds.md), "Read the lock, and approve the release" |
| Deploy | `take` the release to `data/releases/served`, then `fly deploy` with `--depot=false` and `--build-arg RELEASE_ID=lon-2026-10-02-01`. Then build the website again | [Deployment](../deploy/README.md), "Serving a release of London" |
| Go back at once | Deploy the image before, by its name: the release is inside the image | [Deployment](../deploy/README.md), "Going back to the release before" |
| Go back to any release you approved | Take it and deploy it again. Its lock is still committed, and its files are still kept | The same |
| Stop a release from being served again | `git rm` its lock, and deploy another over it | The same |

## 9. What is done by hand each time

Nothing runs on a clock, and nothing starts by itself. **Every step above is started by you.**

| By hand | Why |
|---|---|
| Running `fresh` | No workflow runs it |
| Looking at each publisher's page | No step asks a publisher whether a file changed. `fresh` counts days and knows nothing else |
| Changing the list and the registry entry for 48 of the 88 files | The list pins the edition, the period and often the address |
| Saving four files in a browser | Their publishers give them from a form |
| Bringing the receipts back, and committing them | No workflow may write to the repository |
| Starting and approving each run | A job that is given a key waits for you, by design |
| Taking two releases, and running `moved` | A run may show counts and no name, and the run that builds holds no release to compare with. |
| Committing the lock, and deploying | To approve is yours alone, and no workflow may install the host's program |
| A fetch that found nothing new | It leaves no record, so the file stays due. Note it yourself |
| The names a person decided | A hosted build makes its own draft of names from the store, and reads no decision of the desk |

## 10. What rhythm is sensible

Of the 99 measures of the build of 2026-09-25, 59 rest on a file that changes monthly, 12 on one that changes weekly or daily, 10 on a quarterly one, 6 on a yearly one, and 12 on none that changes more than rarely. The file of places alone stands behind 57.

| How often | Do | Why |
|---|---|---|
| Each quarter, late in February, May, August and November | The whole of this guide, for every file that is due | The postcode directory comes out in those months, and Ordnance Survey's files in April and October, with its names each quarter. A quarter is also what the registry says Burro plans for the timetables. Bring the release of places forward each time: it is monthly, its list pins it, and most measures rest on it |
| Each month, if prices matter to the searches you watch | Steps 2 to 8 for `m2-living` alone | Prices paid, the house price index and the rents index are monthly |
| Once a year, in the autumn | Fetch the traffic counts again, by the list `m13-road-traffic` | The Department for Transport adds a year of estimates to the file once a year, alongside its yearly figures of road traffic. No page that was read states the day, so `fresh` calls the file due a year after it was fetched |
| Once a year | Read the page of each of the 16 sources that change rarely | `fresh` never calls them due. The publisher of one, land use, plans to publish again by the end of 2026, which is not settled |
| After a change to the network | A refresh of `m5-journeys` and `m12-public-transport` | Once a journey is routed, a timetable that is old is a journey that is wrong |
| Never weekly | | 44 files change weekly or daily, and 39 of them need no change to a list. A refresh still costs a fetch, two pushes, two approvals and a deploy |

## 11. What a fresh build can break

| What changed at the publisher | What you see | What to do |
|---|---|---|
| The columns, the sheets or the layout of a file | The build stops: `step=assemble status=refused input_is_as_described=1` | The step that reads the file is changed to read the new layout, with a test on a made-up file of the new shape. Never loosen the check |
| A kind or a category the code has not met | The build stops, and names the rule | A person says what the new kind is, in the table of kinds |
| A file that no longer covers part of London | `moved` shows a measure with many `lost`, or `measures_went` | Read the coverage report beside the release before you approve |
| A boundary that moved | `areas_redrawn`, `areas_came` or `areas_went` above nought | The census areas are fixed until the next census, so none should. Boundary-Line is put out twice a year, and the draft of names reads its wards: a ward that moved shows as a name that changed |
| A name that changed | `areas_renamed` above nought | Every name is a draft until a person has checked it. Read each at the desk |
| The address of a file | The fetch ends `status=failed` or `status=refused why=18` | Item 2 of step 2 |
| A series that ended | The fetch ends `status=failed`, with what the publisher answered after `http=`, or the page names no newer edition | Begin the entry's `cadence` with `Frozen`, and decide whether the measure stays |
| Figures that did not change, in bands that did | `vibes_moved` with no measure moved | A band is a place among London's areas. One area's new figure moves the band of others. Where `parts_came`, `parts_went` or `shares_changed` is above nought it is the recipe that changed, and the publisher changed nothing |
