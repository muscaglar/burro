# Data builds: what to set up, and how to run one

For the founder. Written 2026-09-23. It applies [ADR 0015](adr/0015-where-builds-run-and-what-gates-a-launch.md) and section 3 of [the plan](design/london-data.md).

No workflow here has run yet. Every time below is an estimate. What only a first run can show is listed in section 12. What was read, and where, is in section 14.

The files of nine lists have since been taken to a store that is a folder, by the step `fetch` or from a person who saved them, and two previews of London were built from them. Sections 15 and 16 say how to build each and see it. [Refreshing London](refreshing-london.md) puts the steps of a refresh in one order, from what is due to what is served, and [Adding a city](adding-a-city.md) says what a second city would take. [The report of the first build](research/data/m1-first-build.md) and [the page on the second](research/data/m2-second-build.md) say what each holds.

## Where things stand

As of 2026-09-23, on the branch data-m0. Read this first. What follows under this heading is how things stood before the first fetch. It is what the hosted workflows still wait on. What has changed since is said first, and in the steps that a change touches.

### What has changed since the first fetch

| What | How it stands on 2026-09-24 |
|---|---|
| A fetch | The step `fetch` was run outside a workflow, into a store that is a folder. It fetched files of twelve lists, and four files were saved by a person. No hosted run has fetched a file, and no object store exists |
| Receipts | 87 are in `data/receipts/`, each of a file of a list: the eleven of list m1, all 45 of m2-places, 15 of the 18 of m2-living, all three of m12-public-transport, two of m10-health, two of m11-age-and-households, both of m11-outdoor-space, two of m2-culture, which takes one file of places twice, the second time with the brand of each place, and one each of m10-land-use, m11-high-streets, m12-household-income, m2-stations and m5-journeys. 33 of them are of the food hygiene register, one for each authority, and four are of files a person saved. Three files of the lists have none: the street extract, and the workbooks of sales and of the lower quartile. The workbook of median prices was fetched again on 2026-09-24, and its receipt is for the use the list names |
| List m1 | It states the edition and the period of every file, and `plan` reads `ready=11`. A program read each file, and no person has. Section 7 asks that a person read a file before its receipt is written. Decide whether what a program read is enough, or put both names back under `unsure` and take the item out of `READ_IN_THE_FILE` |
| Two more lists | `m2-places` and `m2-living`. `plan` reads `ready=45` of 45 files and `ready=18` of 18: the three yearly files of prices paid have their addresses since 2026-09-24, and each was fetched that day and has its receipt |
| Ten later lists | `m10-health`, `m10-land-use`, `m11-age-and-households`, `m11-high-streets`, `m11-outdoor-space`, `m12-household-income`, `m12-public-transport`, `m2-culture`, `m2-stations` and `m5-journeys` hold sixteen files between them. `plan` reads all sixteen ready. The pharmacy list states its period since 2026-09-24, as the quarter its publisher's title names. It was fetched again that day, and has its receipt. The lookup between the census areas of 2011 and of 2021 and the timetables were each fetched on 2026-09-24 and kept with no receipt, until the list of each stated its edition and its period, and what `describe` gave of the file. Each was fetched again that day, was the same file, and has its receipt. The lookup states neither, so both are its record's. The timetables state both: the day in the names of the zips the file holds, and the days its services say they run on. They are replaced each week under one address: read the next issue with `describe --inside`, and state both again, before a fetch that would take it |
| Files that state their own edition | 37 files of those two lists have no edition on their publisher's page, and were kept with no receipt. The lists now say where each file states its own, and fetch reads it in what arrives: section 7, "A file that states its own edition". All 37 read ready. The town centre boundaries give the day the file was last changed, and fetch takes no period from it: the list states the period as that day, because a boundary is as the file holds it, and its notes say what was read. A program read it, and no person has. 36 of the 37 have a receipt since they were fetched again, on 2026-09-24: the 33 files of the food hygiene register, two reports and the town centres. The street extract has none. Two more files state no edition and joined the list with an address on 2026-09-24: conservation areas and listed buildings. Each is dated by the day it was retrieved, and has its receipt |
| A build that reads a file which states its own edition | `seal` and `preview` take one edition of such a file, by a rule, and the lock says which: section 7, "Which edition a build takes". The second preview now seals the 33 files of the register. No measure reads them yet |
| The hosts a download is sent on to | Lists m1 and m2-places name four under `may_redirect_to`, as a fetch saw them. The list m10-health names one more, the store the pharmacy list is handed out from, and the receipt of that file bears it out |
| The addresses of files | 45 of the 128 entries name them under `file_urls`: every entry behind a file of a list whose address the list holds, and the four behind a file a person saved |
| Steps that read a real file | `cells`, the measures under `derive`, and `preview`. Two previews of London were built: sections 15 and 16 |
| The draft of the areas | `python -m burro_pipeline.areas.draft_run --out FOLDER` makes the names and the borders of London's areas from the store, in one command. It is a draft: a method made it and nobody has checked it. Nothing of it is committed |
| A hosted build of London | Since 2026-09-25 a workflow builds London from the store in the bucket, on two runners, keeps the release in a bucket of its own where the two builds are the same, and shows its lock. A release is served only once you have committed its lock. The workflow has never run, and no bucket of releases exists: [London, from the bucket to the service](#london-from-the-bucket-to-the-service), after section 14 |
| The review desk | `make desk` starts it. It is filled from a draft with `make desk-fill`. Names are decided before borders: `packages/pipeline/AGENTS.md` says why |
| The check of a release | It asks the gate again about every file a row rests on, for the use the figure is put to, and holds a row to the method and the file of its measure. Both previews pass it |
| The check of what the store holds | The workflow `data-held` says, list by list, whether the store holds every file that the repository holds a receipt for. It fetches nothing, and writes nothing to the store: section 7, "See that the store holds every file that has a receipt". It has never run. The step it runs was driven on 2026-09-25 against the store that is a folder, which holds each of the 87 files that have a receipt |

### How things stood before the first fetch

**No real file has been fetched.** No step of the pipeline has sent a request to a publisher's host, downloaded a dataset or opened a real file. No workflow has run, and no store exists. Everything below was tried on made-up files. Nothing was tried on the platform of record, which is the hosted runner.

A few real files were opened for research, and by no step of the pipeline. File 8 of the Indices of Deprivation: `docs/research/vibes/grit.md` says what was read in it, and that no copy of it was kept. The statistics office's workbook of rents in London: `docs/research/reports/housing-cost.md`. Part of one release of Overture Places: `docs/research/data/overture-places.md`. None is in the repository. No hash was written down, so nothing shows that a file a fetch will store is the file that was read, and no receipt is written from any of those readings.

Burro relies on the licence each publisher has published, as the registry records it. No step of a data build waits for anybody outside to answer.

### What milestone M0 has built

M0 is "ready to fetch": what must exist before the first real file is downloaded.

| Part | What exists | How far it was tried |
|---|---|---|
| The licence registry | The heading `residents` and the use `census_table`. The use `scoring` on the three geography sources behind the first five measures. In each entry behind the first build, the addresses of its files, under `file_urls` | `make registry-check` passes. What was read for an entry is in the entry |
| Fetch | It asks the registry before every file, and holds each file to the entry of its source. One https request for each file. A store as a folder, and as an object store. A file saved by hand. The shape of a file, for a person's own machine | Against a stand-in on the loopback address. It has never met a publisher or an object store |
| The receipt | One record of a fetched file, written by fetch and read by every other part. A copy is kept in the store beside the file. It is written once a person has read the file, and not before: section 7 | On made-up files |
| Evidence | The method, the evidence row and the claim. The lock of a build, sealed from the list of its files. The coverage report. The rule that no fact is served without evidence | On the synthetic release, and on made-up files that were fetched |
| The command line | One command with a step for each part of the work: `uv run python -m burro_pipeline --help`. Each step answers `--help`. The Makefile has a target for the steps a person runs | Every step was driven by hand |
| The hosted workflows | A workflow that fetches and one that builds, and the tools that keep a row, a key and the store's address out of a log. A run installs the pipeline and what it needs, and nothing else | Held to their rules by a check and by tests. Never run |
| The first list | The eleven files of the first real build, each with its registry entry, the page a person finds it on, and its address. Each address was read on its publisher's page through a reader that extracts the text. The list is sure of four, and names seven to be opened once in a browser. It is sure of no edition and of no period, because no file has been read | The registry allows every one. No fetch has tried an address |
| The walk | A test that takes made-up files through every step: served, fetched through the gate, stored, given a receipt, described, sealed, a figure worked out by one method, its evidence written, the report run, and the figure traced back to the hash of its file. Then each link is broken in turn | It passes, and was walked by hand too |

### What M0 has not built

| Not built | It matters because | It waits on |
|---|---|---|
| Any step that reads a real file: normalise, cells, derive | No figure can be worked out from a fetched file. The one method in the walk is part of a test | The first fetch, which shows what the files hold |
| Evidence and coverage inside a release | The API cannot serve the evidence behind a fact | The next schema of the contract |
| A way for a receipt or a lock to reach git from a hosted run | A run may not write to the repository. A person brings the receipts back and commits them: section 7 | Your decision 2 of the plan |
| A release sent to the store, and the full log of a step kept there | A build in a hosted run is thrown away | The first real build |
| A command installed under a name of its own | Steps are run as `uv run python -m burro_pipeline STEP`. A name of its own is one line in the package's manifest, and that line is not yet added | Nothing. It is added with the next change to the manifest |

### What is known and not yet mended

Each was found by reading the code and by trying it on made-up files. None stops the fetch of list m1. Each is to be settled before the first real build.

| Known | What it means | Until it is mended |
|---|---|---|
| The list names the hosts a request may be sent on to, under `may_redirect_to`. The registry entry does not | A change to a list alone can widen where a file may come from | Read a change to `may_redirect_to` as closely as a change to an entry. Lists m1 and m2-places name four such hosts, and m10-health one |
| On a host that only the list names, fetch refuses a file only if it came from an address that some entry names. 83 of the 128 entries name no address for their files | A file of one of those entries that is kept on such a host would not be told apart | The same. And name the addresses of an entry's files before a list names a host it shares |
| `seal` puts a file in the lock for any use the gate allows, an internal use included | A file read to validate against is an input of the build | `check` names every row that rests on such a file, under `input_is_allowed`. No figure may rest on it |
| `write_release` asks the gate about the sources a release names, and reads no evidence | A source that is named only in the evidence is not asked about when a release is written | `check` asks about it. Run `check` on every release, with its lock and the registry. Evidence inside a release is for the contract's next schema |
| `check` asks a source behind a journey for `routing`, and one behind a name for `gazetteer` | The weights and the lookup behind a journey must be registered for `routing`, as ADR 0016 has them registered for `scoring`. No entry has been changed for it | The first real build carries no journey. Decide before the first that does |

### What you must do, in order

Steps 1 to 3 are done before the push, with no key and no run. Step 4 is the push. Steps 6 to 12 are done on two websites and on a machine of your own, and none needs a push. Step 13 changes the list, which a run reads on `main`, so it goes with the second push.

| # | Do this | Where it is said how | Time | A push |
|---|---|---|---|---|
| 1 | Read what this branch changed that waits for you, and approve or change it: the third sentence of rule 8 in `AGENTS.md`, the new registry heading and its rules, the use `scoring` on three geography sources, and ADR 0015 and 0016. Six registry entries rest on a permission in writing, and stay gated until you have filed a note of each reply: the plan, task 25 | `docs/adr/0014` to `0016`. `registry/README.md`, "A permission in writing" | 2 hours, the plan's task 11 | No |
| 2 | Finish the first list. Open in a browser each of the seven addresses the list is not sure of. Put right any that is wrong, and name under `may_redirect_to` any other host a download is sent on to. Where an address holds a query, name each of its parameters under `url_parameters`: a list with a parameter it does not name is refused when it is read. Each edition and each period is stated, because a program has read each file: step 13 says what is left for a person. `uv run python -m burro_pipeline plan --list m1 --words` says what each file still needs. It reads `ready=11` today, and `ready=11` when every file has been read and its edition and its period are stated | `packages/pipeline/src/burro_pipeline/fetch/lists/m1.toml`. Its first lines say which seven, and why | Not known. Nobody has looked | No. It goes with the first push |
| 3 | Run `make ci`. Bring the branch into `main` | | 10 minutes | No |
| 4 | Push the repository to GitHub as a public repository. Turn Actions on | Section 1. The push is yours to make | 1 hour, the plan's task 1 | **The first** |
| 5 | If GitHub refuses the push because of a secret: one test holds the example secret that Amazon prints in its own documentation, to check the signing of requests. It opens nothing. Decide whether it stays. Do not work round the refusal | `packages/pipeline/tests/fetch/test_s3_signing.py` | | |
| 6 | Make the environments, each with you as its reviewer and `main` as its only branch | Section 2 | 25 minutes | No |
| 7 | Make the bucket, its lock, the fetch key and the key of the check | Section 3 | 30 minutes | No |
| 8 | Store the four made-up secrets of the build | Sections 4 and 5 | 5 minutes | No |
| 9 | Do the rehearsal, and read what the run shows | Sections 5 and 12 | 15 minutes | No. What it shows to be wrong is mended together, in one push |
| 10 | Make a contact address that is not your own, and store the five secrets of the fetch and the four of the check | Section 4 | 15 minutes | No |
| 11 | Start the fetch, for every file of the list. It writes the receipt of a file whose edition and period the list states. A file that names either under `unsure` is stored with no receipt, and the run then ends red. That is meant | Section 7 | 5 minutes | No |
| 12 | Save by hand any file that a publisher would not give the runner | Section 7 | Not known | No |
| 13 | Read each file, on a machine of your own. State in the list the edition and the period you found in it. For list m1 a program has stated both, and no person has read a file: read each of the eleven, and put right what is wrong | Section 7, "The first fetch of a file writes no receipt" | Not known. No person has opened a file as a fetch stored it | It goes with the second push |
| 14 | Start the fetch again. It writes the receipts that are not yet written | Section 7 | 5 minutes | **The second**, before it |
| 15 | Bring the receipts back from the store and commit them | Section 7 | 5 minutes | No. They wait for the next push |
| 16 | Start the check of what the store holds. It ends green where the store holds every file that has a receipt in the repository | Section 7, "See that the store holds every file that has a receipt" | 5 minutes | No. It reads the receipts on `main`, so it follows the push that carries them |

If step 2 is left undone a fetch still runs. Every file is asked for at the address the list holds. A file whose address is wrong ends `status=failed`. A file whose edition or period the list names under `unsure` is stored with no receipt, `status=missing why=6`, whether or not step 2 was done.

### How many pushes

| Push | It carries | What it lets you do |
|---|---|---|
| 1 | The branch as it stands, brought into `main`, with the first list finished | The environments, the secrets, the rehearsal, and the first fetch of all eleven files, which stores each and writes no receipt |
| 2 | The list, with the edition and the period of each file as they were read in the file. The steps that read the fetched files, and a build workflow that reads the store | The second fetch, which writes the receipts. A hosted build of the first real release |
| 3 | The receipts, and the lock and the reports of that release | To approve a release is to commit them (ADR 0015) |

- **One push** takes you to the first fetch, with every file of the first list in the store and none with a receipt.
- **Three pushes** take you to the first real map of London that is built in a hosted run and approved. That is the least, if nothing needs mending. The second and third are not built, so their number is an estimate. If a build must find the receipts in the repository before it runs, they go in a push of their own, and it is four.
- A first map on your own screen, from a development build made on a machine of your own, would need only the first push. Whether a release may be opened that way is open: the plan, section 14, row 1.
- No step here asks for a push so that a run can start. A run is started with inputs: the list, and one item of it.

What is mended with no push:

| What is wrong | Mend it |
|---|---|
| A secret was pasted badly | Paste it again on GitHub: section 4 |
| An environment has no reviewer or no branch rule | Set it on GitHub: section 2 |
| A run failed for a reason that may pass: a publisher was slow, the package index did not answer | Run it again from the run's page, and approve it again. From memory, the button reads "Re-run failed jobs" |
| A publisher refuses the runner | Save the file by hand: section 7 |
| An address in the list is wrong | Save the file by hand from the right address. Its receipt records where it was saved from. Put the list right in your next commit |
| A run must be started from a branch that is not `main`, to see it refused: section 12, row 8 | Make the branch on the website, and delete it after. From memory |

What needs a push, and is kept for the next one: a change to a workflow or to a tool, a new list, a new step, and a new day for the packages (section 10). None is urgent unless a run fails without it.

## 0. In short

| Question | Answer |
|---|---|
| What you make | Four environments on GitHub. One bucket, one lock and two keys at the store. Seventeen secrets: five for a fetch, four for the check of what the store holds, four made-up ones for a build, and the same four made-up ones for the routing |
| How long it takes | About 1 hour and a half, once |
| What it costs | GBP 0 to set up and GBP 0 a month at first. Under GBP 1 a month once the store holds 40 GB (section 11) |
| How many pushes it needs | One, to the first fetch. Three, to the first release you approve |
| How a run starts | By hand, from the Actions page of the website. Never from a push, a pull request or a clock |
| What a run asks of you | One approval. A build of the synthetic release then takes about 10 minutes |
| What a run installs | The pipeline and what it needs: today nine packages from outside, and none published after the day its workflow states (section 10) |
| What a run shows | Step names, counts and hashes, under names from a list. Never a row, a key or the address of the store |
| What a run uploads to GitHub | Nothing |
| What a build of London adds to what you make | One environment, one bucket, three keys and eight secrets: [London, from the bucket to the service](#london-from-the-bucket-to-the-service), after section 14 |

Four workflows exist: `data-fetch`, `data-held`, `data-build` and `data-travel`. The second fetches nothing: it says whether the store holds every file that has a receipt. Today a build builds the synthetic release, which is made up, and reads no store. The routing routes the made-up town, and reads none either. Section 13 says what is not built.

One more workflow builds London from the store, and keeps what it built: `data-london`. It has an environment of its own, which holds real keys. [London, from the bucket to the service](#london-from-the-bucket-to-the-service), after section 14, is the whole of it, in the order you do it.

## 1. Before you start

| You need | Why | Time |
|---|---|---|
| The repository on GitHub, public, with Actions turned on | On a free plan GitHub offers environments for public repositories only (read) | Task 1 of the plan |
| The five workflow files on the default branch, `main`: `data-fetch`, `data-held`, `data-build`, `data-travel` and `data-london` | The "Run workflow" button is shown only for a workflow that is on the default branch (read) | They arrive with the push |
| A Cloudflare account with R2 turned on | The store is an R2 bucket | 10 minutes. Cloudflare may ask for a payment card. That was not read |
| A password manager | Each key is shown once | |

## 2. On GitHub: four environments

About 25 minutes. An environment holds the secrets, and makes a job wait for you.

There are four, so that a build is never given the key that can write a raw file, the check of what the store holds is given a key that can write nothing, and the routing is given a key of its own the day it reads the store.

| Environment | Used by | Holds |
|---|---|---|
| `data-fetch` | The workflow `data-fetch` | The fetch key |
| `data-held` | The workflow `data-held` | The key of the check, which may read and list the store and no more |
| `data-build` | The workflow `data-build` | Made-up values, and no key. No step of a build reads the store yet |
| `data-travel` | The workflow `data-travel` | Made-up values, and no key. It routes the made-up town, which reads nothing |

Make each one the same way. The names must be exact.

A build of London has one more, `data-london`, which holds two real keys. It is made the same way, before the first build of London: [London, from the bucket to the service](#london-from-the-bucket-to-the-service).

1. Open the repository, then **Settings**, then **Environments**, then **New environment**.
2. Type the name. Press **Configure environment**.
3. Tick **Required reviewers**, and add yourself.
4. Leave **Prevent self-review** unticked. With it ticked you could not approve a run that you started, and you are the only reviewer.
5. Untick **Allow administrators to bypass configured protection rules**.
6. Under **Deployment branches and tags**, choose **Selected branches and tags**, and add one rule: `main`.
7. Save. The secrets come in section 4.

Make each before the first run of its workflow. If a run names an environment that does not exist, GitHub makes it, with no reviewer, no rule and no secret (read). Such a run is given no secret, because none is stored, but the environment it leaves behind must then be given its rules by hand.

Nothing in a run checks that an environment has its reviewer and its branch rule. If a job that should wait for you starts by itself, stop the run and look at the environment's settings before anything else.

| Setting | Set to | Why |
|---|---|---|
| Required reviewers | You alone | A job that is given a key waits until you approve it, every time |
| Prevent self-review | Off | You start the run and you approve it. Turn it on the day a second person can approve |
| Administrators may bypass | Off | So that nobody skips the wait, you included |
| Deployment branches | `main` only | A workflow changed on another branch is refused the keys |
| Wait timer | None | |

### Who may approve

You, and nobody else, for now. GitHub allows up to six reviewers, and one approval is enough (read).

Anyone who can write to the repository can start a run, and can change a workflow. The approval is what stands between a changed workflow and a key. So before you approve, look at the commit the run was started from: it is on the run's page. If anything under `.github/workflows/` or `tools/` changed since the last run you approved, read the change first. So too for a change to any `pyproject.toml`. Read a change to the line named "Install" with most care: it says what a job that holds a key will run (section 10).

When a second person is given write access: protect `main` so that a change needs a review, and keep yourself as the only reviewer of every environment.

### Two settings to check once

| Where | Setting | Set to |
|---|---|---|
| Settings, Actions, General, Workflow permissions | What the run's own token may do | Read repository contents. Each workflow asks for what it needs |
| Settings, Secrets and variables, Actions, Repository secrets | | Put no secret of the store here. A repository secret is given to every workflow, and `ci.yml` runs on pull requests |
| Settings, Secrets and variables, Actions | Debug logging | Store no secret and no variable named `ACTIONS_STEP_DEBUG` or `ACTIONS_RUNNER_DEBUG`. Either turns debug logging on for every run (read) |

## 3. At the store: one bucket, one lock and two keys

About 30 minutes. The store is Cloudflare R2, which the plan already names.

### The bucket

1. In Cloudflare, open **R2**, then create a bucket.
2. Name it with a part nobody could guess, such as `burro-raw-` and eight random letters and digits. A name is 3 to 63 lower-case letters, digits and hyphens (read). The name is a secret here, and a run fails any step that prints it. So a plain word such as `raw` would fail steps that printed no secret.
3. Choose a location in Western Europe. Do not set a jurisdiction unless you have decided to: it changes the address.
4. Leave public access off. A bucket is private unless you make it public (read). Never turn on the public address of a bucket, and never give a bucket a domain.

### The lock: what is stored is kept as it is for 90 days

Cloudflare offers four permissions for a key (read). None is named as one that may write and may not delete, and the page does not say whether a key that may write may delete. So take it that the fetch key can. What Cloudflare offers is a lock on the bucket: "Bucket locks prevent the deletion and overwriting of objects in an R2 bucket for a specified period — or indefinitely" (read). A lock holds against every key, the fetch key included.

The lock is for 90 days, and not for good. Two kinds of file must be able to go. A register may hold the names of people who trade under their own name, and a person may ask to be erased from what Burro holds. A file may be used by its owner's permission, and the owner may take it back. A file that can never be deleted is one Burro could not stop holding.

Make two rules, before the first fetch:

1. Open the bucket, then **Settings**, then the part on bucket locks, then **Add rule**.
2. Name the rule `raw`. Give it the prefix `raw/`. Choose to keep files locked for 90 days. Save.
3. Add a second rule the same way, named `receipts`, with the prefix `receipts/`, for 90 days too.

If the rules were made with no end, make each again for 90 days: take the rule off and add it again, the same day. It deletes nothing. Whether a rule can be changed where it stands was not read.

| | |
|---|---|
| What is under `raw/` | Every publisher's file, under the id of its source and then its hash |
| What is under `receipts/` | The copy of each receipt, under the id of its source |
| What the lock changes for a fetch | Nothing. A fetch asks whether a file is there before it writes, and writes only if nothing is there. It never deletes |
| What the lock stops | For 90 days: a key that has been seen, or a workflow that has been changed, from deleting a file or putting another in its place |
| What the lock does not stop | A new file written under a new name. A key that has been seen can still fill the bucket, and can still read it. Once the 90 days of a file have passed, take it that such a key can delete the file, or put another in its place |
| Why 90 days loses nothing | The hash and the size of every file are in its receipt, and the receipt is committed. A build copies each file out of the store and holds the copy to its receipt. So a file that was deleted, or that had another put in its place, is found by the next build, which stops and writes nothing: `file_is_in_the_vault`. The lock was never what told a build that a file is the one that was read. It keeps a file from going in its first weeks, when a build is most likely to be made from it |
| What is lost if a file goes after 90 days | The file, if its publisher no longer gives that edition. No figure is changed by it: a release holds its figures and the hash of each file, and a build that cannot find a file makes no release |
| Who can take a rule off | You, in Cloudflare. The fetch key cannot, as far as was read: to change a bucket's settings is named only under the "Admin" permissions |
| When you would take one off | To delete a file that is younger than 90 days: the part "Who can delete a file, and how" says when and how. Or to put a receipt right, and then the rule `receipts` alone: section 7. Put the rule back the same day |

What was not read, and what a first fetch shows instead:

| Not read | How it is shown |
|---|---|
| Whether a key with "Object Read & Write" may delete a file. The page names "read, write, and list objects", and does not name deleting | Taken here as yes. For 90 days the lock is what is relied on, and after them the receipt |
| What the store answers when a locked file is deleted or written over | After the first fetch, try to delete one file in Cloudflare with the rule on. It must be refused |
| From which day the 90 days of a file are counted | Taken here as the day the file was stored. Store one made-up file on the day of the first fetch, and try to delete it on the 91st day |
| Whether a rule made after a file was stored holds that file too | Make the rules before the first fetch, and it does not arise |
| Whether a rule that is made again holds what was stored before it | Try to delete one made-up file that was stored before, with the new rule on. It must be refused |
| Whether the copy of a receipt can be deleted once the rule `receipts` is taken off, and whether the rule put back holds what was stored before it | The first time a receipt is put right: section 7. Try it once on the receipt of a made-up file |
| Whether a lock costs anything | Section 11 |
| Whether a key can be made that is held to less than "Object Read & Write". Cloudflare names short-lived keys made from a key, "scoped" to less (read). How much less was not read | Not used here |

### Who can delete a file, and how

This is not legal advice. It says what Burro does with a file it must stop holding, so that nothing goes without a record and no build goes on as if the file were there.

| | |
|---|---|
| Who | You, and nobody else. No workflow deletes a file, no step of the pipeline does, and no key of a workflow is used for it. It is done by hand in Cloudflare, signed in as the owner of the account |
| When | A person asks to be erased from a register that names them. An owner withdraws its permission for a file that is used by it. A licence ends, or the registry bans the source |
| What is never done | A file is never changed, and another is never put in its place. A commit that has been pushed is never rewritten: a receipt holds a hash, an address and a day, and no row of its file, so the history may keep it |
| What it costs | One commit, which goes with your next push. About a quarter of an hour at the store, which is an estimate |

Do it in this order. The record is written first, so that nothing is deleted without one.

1. **Stop every build from reading the file.** For a whole source: change its entry in the licence registry to `held`, or to `banned`, say why in `status_reason`, and take its items out of every list. Only an approved source may stand behind a release, so none is built on it from then on. For some files of a source that stays: take their items out of the list. The table under these steps says what each change holds, and what the checks then ask for.
2. **Find every file.** The lists are in `packages/pipeline/src/burro_pipeline/fetch/lists/`. An item of a list says in `what` whose file it is, which for a register is the authority, and gives the address of the file in `url`. `data/receipts/`, then the id of the source, holds a receipt for each file, named for its file id. Each receipt gives the hash, the address the file came from in `url`, and the publisher's name for the file. The receipts of a file of a register are those whose `url` is the item's: one for each edition that was fetched. The store keeps the file under `raw/`, then the id of the source, then its hash. It keeps the copy of the receipt under `receipts/`, then the id of the source.
3. **Write the record**, as a note in `registry/evidence/`, named `<source-id>-<yyyy-mm-dd>.md` for the day of the note. The table below says what it holds.
4. **Take the receipts out of the folder** with `git rm`, in the commit that holds the note, the changes of step 1, what the checks asked for, and nothing else. The history of the repository keeps each receipt.
5. **In Cloudflare, delete each file** under `raw/` and the copy of its receipt under `receipts/`. For a file younger than 90 days, take the rule `raw` and the rule `receipts` off first. Put the rule back the same day: both of them, before you close the page.
6. **Delete every other copy**: the folder a build on a machine of your own copied files to, a store kept as a folder, and any second copy of the bucket. Write in the note which were deleted, and on which day.
7. **Build again** every release that rested on a file that is gone, under a new id, and serve the old one no longer. A release is never mended.

What the commit of step 4 holds beside the note. Each row was tried, and undone:

| Change | What it holds |
|---|---|
| The entry of a whole source | `status` becomes `held` or `banned`, and `status_reason` says why and on which day. An entry that is held keeps internal uses alone under `uses`, and one that is banned keeps none: with any other use the registry does not load, and no step runs. `registry/README.md` says what each asks of an entry, and `make registry-check` names what an entry still breaks |
| The lists, for a whole source | Every item of the source is taken out of every list. A fetch asks the registry about its whole list: while a list holds one file that the registry refuses, no file of that list is fetched |
| The list, for some files of a source that stays | The item of each file is taken out. Where the entry of the source names the address of such a file under `file_urls`, the address is taken out too |
| What the checks ask for | Run `make ci` before you commit. It fails at each test that holds a count of what was taken out, and each failure names what it found. For one file of a register that is one number, in `packages/pipeline/tests/fetch/test_editions_a_file_gives.py`. For a whole source, the tests that build from made-up files of that source fail too: to change those is a change to code. Put each right in the same commit |

What record is left:

| Record | Where it is | What it shows |
|---|---|---|
| The note | `registry/evidence/`, named `<source-id>-<yyyy-mm-dd>.md` | The id of the source. The file id and the hash of each file that was deleted. Why, as one of: a person asked to be erased, the owner withdrew its permission, the licence ended. The day you were asked, and the day each copy was deleted. The id of every release that rested on a file, and what became of it. It holds no person's name, no name of a business, no address and no word of what was asked |
| What was asked | It stays with you, outside the repository | Who asked, and in what words. `registry/evidence/README.md` says why such a thing is never saved there |
| The receipts | The history of the repository, up to the commit of step 4 | What each file was: its address, its edition, its hash and the day it was retrieved |
| The change to the registry, and to the lists | The commit of step 4 | That no build reads the source, or those files, from that commit on |

What a build does when a file is gone:

| A build | It does this |
|---|---|
| A step reads a file whose receipt is in the folder, and the store holds no such file, or holds another under its name | It stops: `status=refused file_is_in_the_vault=1`, with the file id on standard error. A build writes nothing: `preview`, `seal` and `cells` are each held to that by a test. The draft of the areas is no build, and may leave in its own folder what its first parts wrote. This was tried on made-up files, with a file deleted, with another put in its place, and with one byte of a file changed and its size the same |
| `seal` is given a receipt of a file that the listing of the store lacks | It refuses by the same rule, and seals no lock |
| A build is made again from the lock of an earlier release, which names the file | The same. A lock names a file by its hash, and nothing stands in for a file that is gone |
| The receipt was taken out of the folder too, as step 4 says | The file is no part of the build. A measure that read it is left out of the release, and its line says `input_has_one_receipt=1`. Nothing is filled in for it. A build that needs the file for its geography stops, by the same rule |
| A release that was built before the file went | It is as it was built: it holds figures and hashes, and no row of any file. `burro-release check` asks the registry as it stands on the day, so it names every row that rests on a source that is now held: `input_is_allowed`. It is built again under a new id, as step 7 says |

What to do, by why the file must go:

| Why | What is deleted | What else |
|---|---|---|
| An owner withdraws its permission | Every file of the source, in every edition, and every copy | The entry becomes `held`, with the day in `status_reason`. Its note of the permission stays in `registry/evidence/`, and the new note stands beside it. Nothing made from the files is shown from the next release on |
| A licence ends, or the registry bans the source | The same | The same, with `banned` where the registry bans it |
| A person asks to be erased from a register that names them | Every file that holds their record, in every edition, and every copy. A register comes as a file for each authority, so that is each edition of one authority's file | The registry lets Burro show no row of such a register, and a release holds counts and no row. So what Burro holds of the person is in the files, and in whatever was made from them by hand: look for both. The register is its publisher's, and a file fetched again may hold the record again. So take that authority's file out of the list until you have decided whether it is fetched again, and say so in the note. It is yours to decide |

### The keys

A key here is what Cloudflare calls an R2 API token. It has an id and a secret, and it is held to the buckets you pick. It cannot be held to a folder inside a bucket (read: the page offers "a set of buckets" and nothing finer).

For each: **R2**, then **Manage API tokens**, then create a token, pick the permission, pick **Apply to specific buckets only**, and pick the bucket.

| Key | Make it | Permission at Cloudflare | Buckets | It may | It may not | Kept |
|---|---|---|---|---|---|---|
| Fetch | Now | Object Read & Write | The raw bucket only | Read, write and list files in the raw bucket | Touch any other bucket. Make, change or delete a bucket. Change a lock | In the environment `data-fetch` |
| Check | Now | Object Read only | The raw bucket only | Read and list files in the raw bucket | Write or delete anything. Touch any other bucket | In the environment `data-held` |
| Reading | On the day you first bring receipts back: section 7 | Object Read only | The raw bucket only | Read and list files in the raw bucket | Write or delete anything. Touch any other bucket | In your password manager, for a machine of your own. Never on GitHub |
| Build | Before the first build of London: [London, from the bucket to the service](#london-from-the-bucket-to-the-service) | Object Read only | The raw bucket only | The same as the reading key | The same | In the environment `data-london`. The environment `data-build` keeps its made-up values: its workflow builds the made-up city and reads no store |

Cloudflare shows the secret of a key once (read). Put the id, the secret and the address it shows for S3 clients in your password manager before you close the page.

Never make a key with an "Admin" permission for a workflow. An Admin key can delete a bucket, and can take a lock off.

### What comes later, and not today

| When | Make | Why not now |
|---|---|---|
| The first build of London in a hosted run | The build key. A second bucket for what a build writes, a key that may write to it and to nothing else, and a key that may read it and no more | Nothing stands in the way: the code is built, and [London, from the bucket to the service](#london-from-the-bucket-to-the-service) says how each is made. Until a build of London is started, a key that is used for nothing can only be lost |
| The census block, M4 | A bucket and a key for tables about residents, in an environment of their own | ADR 0015: a product build can never read them |
| The audit, M6 | Nothing, since 2026-09-25. It was to be a bucket and a key for the audit, in an environment of their own | The proxy audit is dropped ([ADR 0006](adr/0006-rank-places-not-residents.md), as amended), so nothing is fetched for it and nothing is kept for it |
| Any time | A second copy of the raw bucket in another account | The plan, section 14, row 18. It is not set up by anything here |

The plan speaks of three buckets. It needs one more than that, because a key cannot be held to a folder: the raw files and what a build writes must be in two buckets for the build's key to be unable to write a raw file.

## 4. The secrets, by name

About 25 minutes. The four names of the store go in each environment. A fetch has one more.

| Name | What it is | In `data-fetch` | In `data-held` | In `data-build` | In `data-travel` |
|---|---|---|---|---|---|
| `BURRO_STORE_ENDPOINT` | The address Cloudflare shows for S3 clients, whole, beginning `https://` | The real one | The real one | A made-up one: `https://rehearsal-0000.invalid` | The same made-up one |
| `BURRO_STORE_BUCKET` | The name of the raw bucket | The real one | The real one | A made-up one: `rehearsal-bucket-0000` | The same made-up one |
| `BURRO_STORE_KEY_ID` | The id of a key | The real one, of the fetch key | The real one, of the key of the check | A made-up one: `rehearsal-key-id-0000` | The same made-up one |
| `BURRO_STORE_SECRET` | The secret of a key | The real one, of the fetch key | The real one, of the key of the check | A made-up one: `rehearsal-secret-0000` | The same made-up one |
| `BURRO_FETCH_CONTACT` | An email address, or an `https://` page, where a publisher can reach Burro | The real one | No | No | No |

Open **Settings**, **Environments**, the environment, then add each under **Environment secrets**.

A build of London has an environment of its own, `data-london`, which holds two real keys and eight secrets. [London, from the bucket to the service](#london-from-the-bucket-to-the-service) has its table, under "The environment, and its eight secrets". What follows is of the four environments above.

**The build holds made-up values, and no key.** No step of a build reads the store yet, so a build is given nothing that opens it. The step "Every secret is set" of a build refuses a value that could be real: the address must end `.invalid`, which no host can, and every other value must begin `rehearsal-`. The day a step of a build reads the store, its workflow changes, and this table changes with it. A test holds the two together. The routing is the same: it holds the four made-up values until the day it reads a timetable from the store.

**The check of what the store holds has a key of its own, which can write nothing.** Its one step lists the store. Give it a key made with "Object Read only", and never the fetch key: a workflow that is meant to change nothing is then one that cannot. It holds no contact, because it asks no publisher for anything, and the rules check refuses a step of it that would fetch.

`BURRO_FETCH_CONTACT` is sent to every publisher a fetch asks, as part of what the fetch calls itself. It is kept as a secret so that it is in no file and no log. Use an address made for the purpose, and not your own: the plan, section 14, row 16.

- Paste each value whole, with no space and no line break. A run refuses a value that holds either.
- Each value must be at least 8 characters, or a run refuses it: a shorter one cannot be searched for.
- The values are in no file of the repository. Code reads them from the environment, under these names.
- GitHub never shows a secret again. To change one, paste a new value over it.

More secrets come with later milestones: the TfL key, the rail login and two model keys. Each will be named here when the workflow that reads it is written.

## 5. A rehearsal with made-up secrets

About 15 minutes. Do this once, before anything real is stored in either environment.

The build workflow reads no store. So it runs on made-up secrets, and a first run can show all it has to show with nothing real at stake.

1. In the environment of the build, store the four made-up values of section 4.
2. Start a build (section 6). It must wait for you before "Build a" and "Build b" start. If they start by themselves, the environment has no reviewer: cancel the run and go back to section 2. Then approve it.
3. Open the log of each job. Search the page for `rehearsal`. It must not be found. In the step "Every secret is set", a line may read `::add-mask::***`, and must never show what follows the last colon.
4. Read section 12, and note what the run showed for each row.
5. Leave the four made-up values where they are. Only then store the five secrets of the fetch.

If `rehearsal` is found in a log, stop, and tell whoever wrote the workflow. Nothing real has been shown.

Every build after this one is a rehearsal too: it checks the made-up values and hides what is made from them, as a fetch does with real ones. So is every run of the routing, in its own environment.

## 6. Start a build

About 10 minutes for the synthetic release, of which 1 minute is yours.

1. Open the repository on the website, then **Actions**.
2. On the left, choose **data-build**.
3. Press **Run workflow**. Leave the branch as `main`. Press the green **Run workflow**.
4. Open the run. The first job, "Rules and canary", starts at once. It needs no key, so it does not wait for you.
5. When it has passed, the run says it is waiting. Press **Review deployments**, tick `data-build`, and press **Approve and deploy**. One approval starts both builds.
6. "Build a" and "Build b" run side by side. Then "Two builds, one manifest" compares them, and "Search what the run made public" reads the logs.
7. A green run means: both machines built the same bytes, no log holds a planted row or key, and nothing was uploaded. The run's summary page shows the hash of the manifest.

Never tick **Enable debug logging** when you run a data workflow again. What GitHub adds to a log then is not known. If it is ticked, every step that is given a secret refuses to run, and says `status=refused debug=1`.

| Job | Waits for you | Is given a secret | What it does |
|---|---|---|---|
| Rules and canary | No | No | Checks the branch and the workflow files. Installs the pipeline. Plants a marked row and a marked key in copies of the synthetic release, and fails if either can be seen |
| Build a, Build b | Yes, once for both | Only the step that checks the secrets, and they are made up | Installs the pipeline. Builds the synthetic release, and hashes it |
| Two builds, one manifest | No | No | Fails if the two builds differ, and names the file |
| Search what the run made public | No | No. It is given the run's own token, to read the logs | Reads the log of every job that has ended. Fails on a planted marker, on the shape of a store's address, or on any upload. It runs even when a job before it failed |

### Start the routing of the made-up town

About 10 minutes, of which 1 minute is yours. It is started as a build is: choose **data-travel**, run it on `main`, and approve it in the environment `data-travel`.

It works out the journeys of the made-up town from its timetable, twice, on two machines. A green run means: both machines worked out the same journeys and wrote the same bytes, no log holds a planted row or key, and nothing was uploaded. No line names a stop, a place, an area or a time.

| Job | Waits for you | Is given a secret | What it does |
|---|---|---|---|
| Rules and canary | No | No | As in a build |
| Route a, Route b | Yes, once for both | Only the step that checks the secrets, and they are made up | Installs the pipeline. Reads the made-up timetable and checks it. Routes every home point to every place, in four shards, and the first shard twice. Writes the release, and hashes it |
| Two runs, one manifest | No | No | Fails if the two runs differ, and names the file |
| Search what the run made public | No | No. It is given the run's own token, to read the logs | As in a build |

It does not route London. The engine that does is not installed by any package here: [the travel design](design/london-data-travel.md), section 18, says what stands in the way and what the first run of that engine must settle.

## 7. Start a fetch

About 5 minutes of your time. How long the fetch itself takes is not known: the first list is about 2 GB, and the first run's lines say how long each file took.

A fetch takes the files of a list. A list is a file in the repository, under `packages/pipeline/src/burro_pipeline/fetch/lists/`. It names each file, its source in the licence registry, the page a person finds it on, and its address. The first list is `m1`.

1. Open **Actions**, choose **data-fetch**, and press **Run workflow**.
2. Leave the branch as `main`. Choose the list. To fetch every file of the list, leave the item empty. To fetch one file, type its item name as the list gives it, such as `oa-lookup`.
3. Press the green **Run workflow**, then approve the run as in section 6, in the environment `data-fetch`.
4. Read the job "Fetch". It prints one line for each file.

The list and the item are all a run is told. Nothing is committed to start one.

| Step of the job "Fetch" | What it shows | What a green step means |
|---|---|---|
| Install | Words from the installer, and no value | The pipeline and what it needs are installed, and nothing else |
| Every secret is set | `step=secrets set=5 missing=0` | All five are stored and were pasted whole |
| The store answers | `step=store kind=object_store`, then `step=store status=ok files=... bytes=...` | The address and the key are right, and the key may list the bucket |
| Fetch every file, or Fetch one item | `step=store kind=object_store`, then one line for each file, with its registry id, its hash and its size, then one line of totals | Every file asked for is in the store under its hash |

On a line, `status=ok` means the file is stored and has its receipt. Any other status has a number after `why=`. To read what each number means, and what to do about it, run this on any machine, with no key:

```
uv run python -m burro_pipeline why
```

Four things to know before the first fetch.

- **No address has been tried.** Each was read on a page, and none was fetched. The list names the seven it is not sure of. A file whose address is wrong ends `status=failed`, with the reason as a number, and the files after it are still fetched.
- **The licence registry is asked first, about the whole list.** Each file is held to the entry of its source too: its page, its address, and what it names. If one file of the list is refused, no file is fetched, whether or not that file was asked for.
- **A receipt is written on the runner, and the runner is thrown away.** So a fetch keeps a copy of each receipt in the store, beside its file. It is not in the repository until a person brings it back. Section 13, row 3.
- **The first fetch of a file writes no receipt, and the run ends red.** That is meant, and the next part says why.

### The first fetch of a file writes no receipt

A receipt is what a figure on screen is cited to. It states the edition of a file and the period its data describes. Until a person has read the file, both are what a page said of it, and a page may speak of another edition than the file it hands out. So a receipt is written only from an edition and a period that somebody has read in the file itself.

| Run | What it does | What the line of a file reads |
|---|---|---|
| The first | Asks the publisher for the file, and stores it under its hash. Writes no receipt | `status=missing`, with `new=1` and `why=6` |
| The second, once the list states both | Asks the publisher again, finds the same file in the store, and writes its receipt | `status=ok`, with `new=0` |

So the first run of a list ends red, and its last line counts every file that arrived under `missing=`. That is meant. Nothing can be sealed on a file with no receipt, so nothing can be cited to it.

Between the two runs, for each file, on a machine of your own that holds the reading key:

1. Run `uv run python -m burro_pipeline describe` on the file, by the file id its line gave. Open the file itself where that does not show enough: the notes sheet of a workbook, or the first lines of a table.
2. Find in the file its edition, and the period its data describes. Where the file states neither, open the page it came from in a browser, and say in the item's `notes` that the file does not state it and which page does.
3. In the list, state `edition` and `data_period` as you found them, and take both names out of the item's `unsure`. In the same commit, name the item in `READ_IN_THE_FILE` in `tools/tests/test_guide.py`, and change the count that `packages/pipeline/tests/fetch/test_cli.py` expects of `plan`. `make ci` fails until the three agree.
4. Push. A run reads the list on `main`.
5. Start the fetch again, for the whole list or for one item.

Read the line of each file in the second run. It must read `new=0`: the file the publisher gave is the file you read. If it reads `new=1`, the publisher has changed the file since you read it, and the receipt that was written is of a file nobody has read. Put it right as the part "Put a receipt right" says.

What this costs: every file is asked of its publisher twice, which for the first list is about 2 GB each time, and the list is pushed once between the two runs.

### A file that states its own edition

Some publishers put another file at the same address, daily or when they have one, and name no edition on their page. The food hygiene register does so, for each authority. What a list states is written on whatever arrives, so a list cannot state the edition of such a file: tomorrow's file would be given yesterday's day.

For such a file the list states no edition. It says where the file states its own, under `edition_from`, and fetch reads that in what arrives, before anything is kept. It reads that one value and nothing else of the file. So one fetch writes the receipt. No person reads the file first: a program does, as for list m1. Whether that is enough is yours to decide.

| `where` | The file | What is read | The edition | The period |
|---|---|---|---|---|
| `xml_header` | A register in XML | The day in one named element of the header, which is the first element under the root. The list names both, as `Header/ExtractDate` | The list's words and the day: `extract of 2026-09-16` | That day, where the list says so |
| `geopackage` | A GeoPackage | The day its contents were last changed, in `gpkg_contents` | `last changed` and the day | Never read by fetch: that day is about the file. The list states the period. For a file of boundaries, which are as the file holds them, the list may state that same day, and its notes say why |
| `street_extract` | The street extract | The time its first block says its data runs to | The time, as its publisher writes it | The day of that time |
| `retrieved` | A file that holds no date | Nothing | `retrieved` and the day of the fetch | That day, where the list says so: the report is made when it is asked for |

The receipt says where its edition was read, under `edition_from`. A receipt of an edition that a page stated does not hold the field, so a reader can tell the two apart.

| What arrives | The line of the file reads | What is kept |
|---|---|---|
| The file that has its receipt: the same bytes, the same edition | `status=ok`, with `new=0` | Nothing new. The receipt stands as it was |
| A new file that states a new edition | `status=ok`, with `new=1` | The new file and a receipt of its own. The old file and its receipt stand beside it: a build's lock names which it used |
| A new file that states the edition of a file of the same item that has its receipt | `status=refused`, with `why=35` | Nothing. One edition is one file, so this should not be |
| A file that holds no day where the list says, or holds it twice, or holds what is not a day | `status=missing`, with `why=34` | The file, with no receipt. What it held there is not said |

A file that holds no date keeps the day it was first retrieved: the same bytes retrieved on a later day are nothing new.

### Which edition a build takes

Once such a file has been fetched twice, the folder of receipts holds two editions of one file of the list. A build takes one, and never both. The rule is written at the top of `packages/pipeline/src/burro_pipeline/evidence/lock.py`, and is the same for `seal` and for `preview`.

| | The rule |
|---|---|
| Which receipts are of the file | Those fetch could have written from the item of the list: the item's source and use, the list's own address for the file, the place the list says the edition is read in, and an edition that is the list's words and then a day or a time |
| Told nothing | The build takes the newest: the edition that states the latest day. The day is the one the file states, and never the day the file was retrieved |
| Told an edition | `--edition ITEM=EDITION` names the file as the list names it, and the edition as its receipt writes it: `--edition fsa-camden="extract of 2026-09-16"`. Give it once for each file. A file that is not named is taken at its newest |
| What the lock says | Beside the hash of each such file, the name the list gives it and the edition that was taken. The lock alone says what was read |
| What is passed over | The receipts of the other editions. They stay in the folder, and are no part of the build |

The line of `seal` counts what was taken: `own_edition=33 named=0 passed_over=0` says that 33 files were taken by their own edition, that none was named, and that no receipt of another edition was passed over. A note on standard error names each file of which one edition of several was taken. A build that takes no such file prints none of the three.

To build again what an earlier build read, after newer files have arrived: read `item` and `edition` of each input in its `lock.json`, and give each to the build as `--edition ITEM=EDITION`. Built on the same commit, under the same id and the same `--built-at`, it seals the same lock, byte for byte. Told nothing, the build takes the newer files, and its lock says so.

| What you see | Why | Do this |
|---|---|---|
| `step=seal status=refused listed_file_has_one_receipt=1`, or the same from `step=assemble` | Two receipts of one file state the same edition, and are of different bytes. Fetch refuses the second with `why=35`, so one of the two was written by hand or brought from another store | Find which file the publisher gave, and move the receipt of the other out of the folder |
| `step=seal status=refused named_edition_has_a_receipt=1`, or the same from `step=assemble` | An edition was named with `--edition`, and no receipt of that file states it. Or it was named for what is no file of the list that states its own edition | Read the edition in the receipt of the file, under `data/receipts/`, and give it as it is written there |

The files of the register are not of one day. Each authority's file states the day of its own extract, and on 2026-09-24 the 33 files stated seven days between them, from 2026-09-09 to 2026-09-16. So a figure made from all 33 is as at a span of days, and the span is what is shown as its date.

Nobody has tried this on a real file. It was built on made-up files, shaped as the list's notes say each real file is. The first fetch of each of the 37 files is the test. Read its line.

### Bring the receipts back

A figure is cited to a receipt, and `seal` reads receipts from the repository. After a fetch in a run, on a machine of your own that holds the reading key:

```
uv run python -m burro_pipeline receipts
git add data/receipts
```

It writes each receipt under `data/receipts/`, and never writes over one that is there. Its first line says which kind of store it was given, and must read `step=store kind=object_store`. Its last line reads `step=store status=ok receipts=... new=...`. Then commit them, if you have said yes to decision 2 of the plan. They go with your next push: nothing waits for them until a lock is sealed. The step's own `--help` says how the store is named on a machine of your own.

### See that the store holds every file that has a receipt

About 5 minutes of your time. The check fetches nothing, and writes nothing to the store.

A build copies each file out of the store by the hash its receipt gives. So the store holds all that a build reads when it holds every file that the repository holds a receipt for. No fetch says whether it does:

- A fetch says `status=ok by_hand=1` of a file that a person saved, once its receipt is committed. It looks for the receipt, and never for the file.
- A publisher may have put another file at the address since. The fetch stores what arrives, and the file that was read is not in the store.

1. Open **Actions**, choose **data-held**, and press **Run workflow**. Leave the branch as `main`. It asks for nothing else.
2. Approve the run as in section 6, in the environment `data-held`.
3. Read the step "The store holds every file that has a receipt", in the job "What the store holds".

| The step prints | It says |
|---|---|
| `step=store status=ok files=89 bytes=5584175799` | How many files the store holds in all, with a receipt or with none |
| `step=store list=m2-living status=ok files=18 receipts=15 missing=0 differs=0` | One line for each list. `files` is how many files the list names, and `receipts` how many receipts the repository holds of them. A file with no receipt is not asked about: no build reads one. `missing` and `differs` count the files that have a receipt and are not in the store as the receipt has them |
| `step=store list=m2-living source=dfe-gias item=gias-establishments status=missing file_id=f-e2cf7e0c0508` | One line for each such file: its list, its source, its name in the list, and the id of the file, which its receipt is named for. `status=missing` says the store holds no file of that hash. `status=differs` says it holds one, under another name or at another size than its receipt gives |
| `step=store status=ok lists=13 receipts=87 missing=0 differs=0 unlisted=0` | The totals. `status=ok` on this line says that the store holds every file that has a receipt. `unlisted` counts the receipts that are of no file of any list: each is held to the store all the same, and one that is missing has a line with no `list` and no `item` |

A green step means the store holds every file the repository holds a receipt for. A red step ends `exit=1`, and the lines above it name each file that is missing or that differs.

What to do about a file that is named:

| The file | Do this |
|---|---|
| Its item has an address, and no fetch has yet stored it | Start a fetch for that one item, as the top of this section says. Then start the check again |
| A person saved it, or its publisher has put another file at its address since | The file is in the store it was first kept in: a folder, under `raw/`, then the id of its source, then its hash. Hand it over from there with the step `by-hand`, on a machine of your own that holds the fetch key, with the object store named in place of the folder. Give `--file` the file as it lies there, under the name its receipt gives. Give `--url` the address the list gives for the item, or for a file a person saved the `url` of its receipt. Give `--saved-on` the `retrieved_at` of its receipt. The line reads `status=ok`, with `new=1`, and the receipt that is committed stands |
| It is part of a file, which the list names under `take` | Only a fetch writes the receipt of a part. Start a fetch for the item. Where the publisher no longer gives the file the part was taken of, hand the part over as the row above says: the step stores it, and then ends `status=differs` with `why=7`, because it writes no receipt of a part. The receipt that is committed stands, and the check finds the file |
| `status=differs` | Look at the file in Cloudflare, and tell the builder. Never change a file in the store |

The check reads the lists and the receipts as they are committed on `main`. It reads no file: a file is kept under its hash, which is checked as it is stored, and a build checks the hash again of every file it copies out.

To ask the same of a store on a machine of your own, that is a folder or is named with the reading key: `uv run python -m burro_pipeline held --receipts data/receipts`.

### The four files a person saved

`naptan-london`, `gias-establishments`, `police-crime-london` and `postcode-directory` were each saved by a person, and no fetch takes any of them. Each reaches the object store by the step `by-hand`, run on a machine of your own that holds the file and the fetch key, with the object store named in place of the folder. The row "A person saved it" above says what to give the step.

### Put a receipt right

The first receipt of a file stands, in the repository and in the store. No run puts a receipt right: a run that finds a receipt which says something else than the list ends `status=differs`, and writes over nothing. That is what keeps a run from dropping a receipt without a word. So a receipt that is wrong is put right by hand.

| | |
|---|---|
| Who | You, and nobody else. It needs the right to change a lock at the store, which no key of a workflow has, and the right to commit to `main` |
| When | The receipt states an edition or a period that the file itself does not bear out, or does not say where its edition was read, where the list says the file states its own. Nothing else in a receipt is put right this way: a file with another hash is another file, with a receipt of its own |
| What is never touched | The file under `raw/`. Its rule stays on throughout, and the file is the one that was stored first |

1. Bring the receipts back. If the wrong receipt is not yet in the repository, commit it as it is. The history then holds what was wrong.
2. Put the list right: state the edition and the period as the file has them.
3. Take the wrong receipt out of the folder with `git rm`, in a commit that holds this and the change to the list, and nothing else. Write in its message the file id, which of the edition and the period was wrong, what the receipt said, what the file says, and the day the copy in the store is deleted.
4. Push.
5. In Cloudflare, delete the one copy: it is under `receipts/`, then the id of the source, and is named for the file id. If the copy is younger than 90 days, take the rule `receipts` off first. Put the rule back the same day. The rule `raw` is never taken off for this.
6. Start the fetch for that one item. It finds the file in the store and no receipt of it, and writes the receipt from the list as it now stands: `status=ok`, with `new=0`.
7. Bring the receipts back, and commit the new one.

What record is left:

| Record | Where it is | What it shows |
|---|---|---|
| The wrong receipt | The history of the repository, from the commit of step 1 | What was stated, and on which day |
| The correction | The commit of step 3: its message, and its change to the list | Which file, what was wrong, what the file says, who put it right, and the day the copy in the store was deleted |
| The receipt that stands | `data/receipts/`, and its copy in the store | What is stated now. Its `retrieved_at` is the time of the run of step 6, which is later than the first |

Nothing is deleted without a record. The one thing deleted at the store is the copy of a receipt, and only after the receipt itself is in the history of the repository. A commit that has been pushed is never rewritten, so the record stays.

If the copy in the store is left as it is, nothing is lost and nothing is right: every fetch of that file ends `status=differs why=16`, and the step `receipts` ends `status=differs`, until step 5 is done.

A release that was built while the receipt was wrong is built again. The period a figure is cited to comes from the receipt.

### A publisher that refuses the runner

Save the file in a browser, and hand it over with the step `by-hand`, on a machine of your own that holds the fetch key. `uv run python -m burro_pipeline by-hand --help` says how. No workflow does this, and it needs no push.

### The shape of a file: on your own machine only

`uv run python -m burro_pipeline describe` prints the names in a file's own layout: its columns, its sheets, its layers. Of a GeoPackage it prints the day each layer says it was last changed too, as `last_changed`: it is the day a list states as the period of a file of boundaries, where neither the file nor its page states another. Run it on a machine of your own that holds the reading key, before the code that reads the file is written.

- **What it prints is for your own machine, and never for a public log.** It takes the first row of a table for the names of its columns. Where a table has no header, that row is data: a name, a postcode, a price. So treat all it prints as if it held a row.
- **No workflow runs it.** The rules check refuses a workflow that does. If it were run behind the public log, every line of it would be withheld.
- **What a workbook says of itself.** Of an OpenDocument workbook, `--sheet NAME` gives the words of that one sheet as well: each row that holds words alone, with the column each cell stands in. That is its cover, its notes, the title over a table, the rows that name its columns and the notes under it. A row that holds a number is never given, so no figure is. A sheet of text alone, such as a list of names, is given row by row, up to 200 rows.
- **What a timetable says of itself.** Of a timetable in TransXChange it gives how many services the file holds, the earliest day any of them runs from, the latest day any runs to, and the mode of each. It reads no stop, no name of a line and no time. With `--inside` it gives the same of every timetable in a zip, and in a zip inside a zip. It is how the period of a file of timetables is read before the file has a receipt: the period is the days the timetables say they run on, and never the day the file was fetched. On the timetables of Transport for London it takes about two minutes.
- Paste what it prints nowhere that others can read: not in an issue, a pull request, a commit or a chat.

## 8. What a run prints

A step's own words are never shown. Each step runs behind `tools/public_log.py`, which shows a line only if every part of it is a name from the list in that file, followed by a value of the shape the list gives that name. A name that is not on the list is withheld, whatever stands after it: a name can carry a row as well as a value can.

| On a line | Means | What may stand after it |
|---|---|---|
| `step=assemble` | The step's name | A name from a fixed list |
| `status=ok`, `failed`, `refused`, `skipped`, `missing`, `differs`, `unreadable` | How it ended | A word from a fixed list |
| `exit=2` | The code the step returned. 0 is success | A whole number |
| `withheld=5` | How many lines the step wrote that were not shown. It is not a fault: a traceback is withheld too | A whole number |
| `secrets=1` | How many lines held a secret. Any number fails the step. See section 10 | A whole number |
| `files=10`, `bytes=168002`, `n=3`, `ready=10` | Counts | A whole number |
| `ok=9`, `failed=1`, `missing=1` | How many files ended each way | A whole number |
| `source=...` | The source of a file | An id that is in the licence registry |
| `list=m1`, `item=oa-lookup` | A list of files, and a file of one, by the name the list gives it | A name that a list of this repository gives |
| `lists=13`, `unlisted=0` | How many lists the store was held to, and how many receipts are of no file of any list | A whole number |
| `kind=object_store` | Which kind of store a step was given. In a run it never reads `kind=folder` | A word from a fixed list |
| `kind=html` | What arrived in place of a file, where it was not kept | A word from a fixed list |
| `host=...` | A host a request was sent on to: the first twelve digits of a hash of its name, and never the name | Twelve digits of a hash |
| `why=3` | Why a file was not fetched, or has no receipt | A number of one or two digits |
| `http=403` | The status a publisher answered with | Three digits |
| `file_id=...`, `release=...`, `file=...`, `copy=a` | A file by its id, a release by its id, a file of a release, one of the two builds | The shape of each, or a name from a fixed list |
| `manifest_sha256=...`, `sha256=...` | Hashes | 64 digits of a hash |
| `fact_has_a_row=2`, `gate_refuses=1` | How many findings a rule made. The name is the rule's | A whole number |
| `stops=16`, `trips=756`, `running=502`, `calls=2654` | What a timetable holds: its stops, its trips, the trips that run on the day that is modelled, and the calls they make | A whole number |
| `origins=72`, `destinations=40`, `departures=120`, `shards=4`, `pairs=960`, `beyond=995` | What was routed: the home points, the places journeys end at, the departure minutes, the shards, the pairs of an area and a place, and the journeys that are longer than the cutoff | A whole number |
| `times_are_in_order=1`, `engine_is_installed=1` | The rule the routing stopped on. The name is the rule's, and holds nothing of a timetable | A whole number |
| `seconds=0.7` | How long it took | A number. It alone may have a fraction |

A step that starts to print a new count adds its name to the list in the same change. Until it does, the line is withheld, and a test of the step fails.

In "Rules and canary" you will see `status=failed` on two lines of a green step. That is the canary at work: the second and third things it runs are meant to fail, and it checks that they fail without showing anything.

## 9. When a run fails

Open the run, then the job with the red cross, then the step with the red cross.

| The step | The log says | It means | Do this |
|---|---|---|---|
| The run is on the default branch | `a data workflow runs on the default branch only` | The run was started from another branch | Start it again, with the branch left as `main` |
| The run is on the default branch | `error: .github/workflows/...` | A workflow file breaks a rule. The line names the rule | It is fixed in a commit. `make ci` fails on the same line |
| The run is on the default branch | `error: uv.toml: ...` or `error: pyproject.toml: ...` | The repository holds a setting of the installer, or a package that is not taken by its name from the index: section 10 | The same |
| No file names a private package host | `error: ...: contains credentials`, or a count of hosts | A file holds an address it should not | It is fixed in a commit |
| Install | Words from the installer | The package index did not answer, or no version of a package is as old as the day the line states | Run it again. If it fails twice, tell the builder: the day may have to be moved, which is a change and a push (section 10) |
| A planted row and a planted key | `step=canary status=failed` with `found=1` | Something planted could be seen | Stop. Run no fetch. Tell the builder. The data was made up, so nothing real was shown |
| A planted row and a planted key | `uncaught=1` | A step printed a key and was not failed for it | The same |
| A planted row and a planted key | `unread=1` | The release reader could not be run | Tell the builder |
| Build a or b | Nothing. The run says it is waiting | It waits for you | Approve it: section 6, step 5. A run that is never approved fails after 30 days (from memory, not read) |
| Every secret is set | `error: BURRO_... is not set`, `is shorter than`, `holds a space`, `must begin https://` | A secret is missing or was pasted badly | Paste it again: section 4 |
| Every secret is set, in a build | `is not a made-up value`, and `status=refused real=1` | The environment of the build holds a value that could be real | Paste the made-up value of section 4 over it. If it was a real key, rotate that key: section 10 |
| Any step | `status=refused debug=1` | The run was started with debug logging on | Start a new run, with the box unticked |
| The store answers | `step=store status=failed exit=2` | The store did not answer, or refused the key | Check the address, the bucket's name and the key, in that order. Paste them again. If the key was deleted, make a new one: section 10 |
| Fetch | `status=missing why=3` on a file | The list holds no address for that file | Save the file by hand: section 7. Write its address into the list in your next commit |
| Fetch | `status=refused why=1` on a file, and `status=skipped why=2` on the rest | The licence registry refuses the source for that use. No file of the list is fetched | Nothing was sent to the publisher. The step `why` says what would change it |
| Fetch | `status=refused` with `why=12`, `why=13`, `why=18`, `why=14` or `why=15`, and `status=skipped why=2` on the rest | The file is not as the entry of its source has it. 12: the page the list gives is not one the entry holds. 13: the file is on a host the entry does not name. 18: the address of the file is not one the entry names for its files, or the file arrived in the end from an address that another entry holds, or from one that can be read more than one way. 14: the file names a census table about residents. 15: the file is for the audit, or is such a table, and no store is built for either | For 12, copy the page from the entry. For 13 and 18, look at the address in the list first. If it is a file of this source, name its address under `file_urls` in the entry, in a change that you read. Never widen an entry to make a fetch pass. 14 and 15 are meant: leave the file out of the list. Where the refusal came after a file had arrived, that file was not kept |
| Fetch | `status=refused why=19` | The file is a zip, or holds one, that could not be looked into. It was not kept, because what it holds cannot be held to the entry of its source | Open it on a machine of your own and see what it holds. Tell the builder |
| Fetch | `status=failed why=27 http=403` and the like | The publisher refused the runner | Save the file by hand: section 7 |
| Fetch | `status=unreadable why=5 kind=html` | What arrived is a web page and not the file: a sign-in, or terms to accept. It was not stored | Open the address in a browser, and save the file by hand: section 7 |
| Fetch | `status=failed why=28` with `host=` and twelve digits | The publisher sent the request on to a host the list does not name | `uv run python -m burro_pipeline plan --list m1 --words` prints the same digits beside each host it knows. Name the host under `may_redirect_to` in your next commit, or save the file by hand |
| Fetch | `status=failed why=8` | The store refused, or did not answer | As for "The store answers". With the lock on, a file that is already stored is not written again, so the lock is not the cause |
| Fetch | `status=differs by_hand=1 why=7` | A receipt of a file saved by hand says something else than the list says now: the edition, the period or the use. Nothing was written over | Compare the receipt with the list. If it is the list, put the list right. If it is the receipt, put it right as section 7 says, under "Put a receipt right" |
| Fetch | `status=differs why=16` | A receipt of this file is kept in the store, and says something else than the list says now. Nothing was written over, and the run ends red | Bring the receipts back: section 7. Compare the one of this file with the list: one of them has the edition or the period wrong. If it is the list, put the list right. If it is the receipt, put it right as section 7 says, under "Put a receipt right" |
| Fetch | `status=failed why=17` | Fetch stopped on a fault of its own while it worked on this file, and went on to the next | Tell the builder. The step `why` says how to see where the fault came from, on a machine of your own |
| Fetch | `status=failed why=33` | The address of the file, or one the publisher sent the request on to, is not plain ASCII: it holds an accented letter, say. Nothing was asked of that address | Write the address in the list as a browser sends it, or save the file by hand: section 7 |
| Fetch | `status=missing why=6` | The file is stored, and has no receipt, because the list is not sure of its edition or its period. On the first fetch of a file that is meant | Read the file, and state both in the list: section 7, "The first fetch of a file writes no receipt" |
| Fetch | `status=missing why=34` | The file is stored, and has no receipt. The list says where the file states its own edition, and what arrived holds no day there, or holds it twice, or holds what is not a day | Run `describe` on the file, on a machine of your own. Put `edition_from` right in the list: section 7, "A file that states its own edition" |
| Fetch | `status=refused why=35` | What arrived states the edition of a file of the same item that has its receipt, and is not that file. Nothing was kept | Fetch again on a later day. If it still arrives so, tell the builder: the place the list names does not tell one file from the next |
| Fetch | `status=refused why=36` | The list says to take part of the file, and the publisher did not give a piece that was asked for. Nothing was kept | A publisher that gives no pieces gives the file whole: take `take` out of the item, and see that `max_bytes` allows the whole file |
| Fetch | `status=refused why=37` | The file changed at the publisher while pieces of it were taken. Nothing was kept | Fetch again. If a new file stands at the address, see that the list still states its edition |
| Fetch | `status=refused why=38` | The list says to take part of the file, and the file is not laid out so that the part can be taken. Nothing was kept | Run `python -m burro_pipeline why` for what it may be, and put the item of the list right |
| The store holds every file that has a receipt | `status=missing` or `status=differs` on the line of a file, and `step=store status=failed exit=1` | A file that has a receipt is not in the store, or is not there as its receipt has it. Nothing was changed | Section 7, "See that the store holds every file that has a receipt", says what to do about each |
| The store holds every file that has a receipt | `step=store status=failed exit=2`, and no line of a list | The store did not answer or refused the key, or the folder of receipts could not be read | As for "The store answers". The key of the check is its own: section 3 |
| Build the synthetic release | `step=assemble status=failed exit=...` | The build failed. Its words are withheld | Run `make fixture` on any machine: on made-up data it prints the same words |
| Any step | `secrets=1` or more | A step printed a secret. The line was withheld, so the log does not hold it | Rotate the key all the same: section 10. Tell the builder |
| Any step | `withheld=` with a number, and a line you expected is not there | The step printed a name that is not on the list | Tell the builder. The name is added to the list, or the step stops printing it |
| Hash what was built | `step=manifest status=failed file=...` | A file is not what the manifest says | Tell the builder |
| Compare the two builds | `step=compare status=differs file=...` | The two machines built different bytes | The release is not used. Tell the builder which file |
| Compare the two builds | `step=compare status=missing` | A build gave no manifest | Look at the two build jobs first |
| No log holds a planted row | `step=search status=failed` with `found=1` | A log holds a planted marker, or the shape of a store's address | Stop every data run. If it may be the real address or a real key: section 10 |
| No log holds a planted row | `artifacts=1` | The run uploaded something | Delete it on the run's page. Tell the builder |
| No log holds a planted row | `step=search status=unreadable` | The logs could not be read | Run it again. If it fails on a first run, see section 12, row 3 |

Whoever writes the code cannot read why a real step failed, because the log holds counts only. That is open in the plan, section 14, row 2. Until the full log is kept in the store, a failure on real data is found by running the same step on a made-up file shaped like the real one.

## 10. Upkeep: rotate a key, and move the day that packages are held to

### Rotate a key

About 10 minutes.

| When | Which way |
|---|---|
| A log shows `secrets=` with any number, or the search found something | At once, the fast way |
| A machine or a password manager that held a key is lost | At once, the fast way |
| A person who held a key leaves | The same day, the fast way |
| Nothing has happened | Every six months, the slow way. The interval is a guess, and is yours to set |

**The fast way: the old key stops working now.**

1. In Cloudflare, **R2**, **Manage API tokens**: delete the key.
2. Make a new one with the same permission and the same bucket (section 3).
3. On GitHub, paste the new id and secret over `BURRO_STORE_KEY_ID` and `BURRO_STORE_SECRET`, in the one environment that key belongs to.
4. Start a fetch, and see "Every secret is set" and "The store answers" pass.

**The slow way: no run fails in between.** Do step 2, then 3, then 4, and delete the old key last.

If a key may have been seen: look in Cloudflare at what is in the bucket and when it changed. A fetch key can read every file and write new ones. With the lock on, it cannot delete a file that was stored in the last 90 days, or put another in its place. Take it that it can do both to an older file, and to any file with the lock off. The next build finds either: section 3, "Why 90 days loses nothing". A reading key can only read.

If the address of the store may have been seen: it holds the account's id, which cannot be changed. An address alone opens nothing, because the bucket is private and every request needs a key. Rotate every key, delete the logs of that run on its page, and write down what happened.

### What a run installs

A job that holds a key installs only what a step imports. Every job installs with one line, named "Install", and the rules check allows that line and no other.

| | |
|---|---|
| What it installs | The pipeline and the ranking engine, which are this repository's own, and what they need from outside: today `pydantic` and the four packages it needs, `shapely` with `numpy`, and `pyproj` with `certifi`. The last four are for the step that joins outlines, and a fetch installs them too, because a job installs the whole of the pipeline |
| What it leaves out | The development group: the API, the test runner and what they need. With it, an install brings 30 packages from outside, as counted on 2026-09-23 |
| What it brings to build the two packages, and then puts aside | `hatchling` and what it needs. They run while the job installs, before any step is given a secret. How many they are was not counted |
| What holds a version | The line ends `--exclude-newer` and a day. Nothing published after that day is installed (read, in the package manager's own help). The same holds for what a build needs (tried) |
| What it names | No package index. ADR 0008 forbids one in this repository |
| What runs after it | Every later command runs in what was installed, as it stands, or with nothing of the project. Neither installs. A plain `uv run` would bring every package of the workspace up to date first, and the check refuses it |

The installer reads more than the line. Each of these could bring in a package published after the day, with the line left as it is. The rules check holds each, in `make ci` and as the first step of every run.

| What could change what the line brings | How it is held |
|---|---|
| The installer itself. Another version may read the line another way | Every job sets the installer up at one version, which the check states as `INSTALLER`. A workflow that names another version, or `latest`, or none, is refused |
| A setting given to a step. The installer takes most of its settings from the environment of the step, under names that begin `UV_` (read, in its own help). One of them names a settings file | No value is written in a workflow. A step is given a secret, an input, a matrix value, an output, the run's token or the name of the default branch, and nothing else |
| An input given under the name of a setting. Whoever starts a run types an input | An input, a matrix value and an output each go under a name from a short list: `LIST`, `ITEM`, `COPY`, `COPY_A`, `COPY_B`. The token and the default branch each go under their own name, to one step. The step that installs is given nothing |
| A settings file of the installer, `uv.toml`. It can give one package a day of its own (read, in the installer's help, of `--exclude-newer-package`) | The repository holds none: not at the top, and not beside the manifest of a package |
| The installer's settings in a manifest, under `[tool.uv]` | A `pyproject.toml` holds there what makes the workspace, `package`, `workspace` and `sources`, and no other setting. A setting the check has not heard of is refused too |
| A package taken from a file, a folder, a repository or an address. Nothing but the index says when a file was uploaded, so the day does not hold such a package | Under `sources` a package is taken from this workspace, or is not named. What a package needs is named, with its versions, and is never given as a file or an address |

What this does not do:

- It holds a version by the day it was published, and not by its hash. That waits for a committed lockfile (ADR 0008). When there is one, the line gains `--locked`.
- It trusts the index to say truly when a file was uploaded.
- It trusts the nine packages, and the ones a build needs, as they stood on the day stated.
- It does not look outside the repository. The installer also reads a settings file from the folders above the one it runs in, and from the settings folder of whoever runs it (read, in its help). No step of a run can write one there. What the hosted runner holds there has not been seen.
- It does not hold the release of Python. `.python-version` names 3.13, and which release of 3.13 a run is given is not held.

### Move the day

| | |
|---|---|
| Who moves it | You, or whoever writes the code, in a change that you read before you approve the next run |
| When | When a change to the code needs a newer version of a package. When a fault is found in a package that a run installs, and a newer version mends it. Otherwise leave it: an old day costs nothing |
| Where it is written | Once in `tools/check_data_workflows.py`, as `PACKAGES_BEFORE`, and on the line named "Install" of each job that installs: two in each of `data-fetch`, `data-held`, `data-build` and `data-travel`, and three in `data-london` |
| What it costs | One change, and one push. It can wait for a push you are making anyway |

1. Choose a day that has come. A test refuses a day that has not: it would hold nothing back.
2. Change `PACKAGES_BEFORE`, and the same day on the eleven lines. `make ci` fails until all twelve agree.
3. See what the new day brings before you push:

   ```
   uv tree --package burro-pipeline --no-dev --exclude-newer DAY
   ```

   Write the day as the check writes it. The command reads the package index, and writes a lockfile that git ignores. Read the versions it lists against the ones a run installed last. An index that does not say when a file was uploaded has every file refused: then leave this step out, and read the step "Install" of the next run in its place.
4. Commit it with a line that says why the day moved. It goes with your next push.
5. In the first run after it, read the step "Install". If it fails, a package has no version as old as the day: choose a later day.

### Move the version of the installer

Seldom. It is written once in `tools/check_data_workflows.py`, as `INSTALLER`, and on the line `version:` of each job of a data workflow: three in `data-fetch`, three in `data-held`, four in `data-build`, four in `data-travel`, four in `data-london`. `make ci` fails until all nineteen agree. `ci.yml` names its own, and is not held to it. Before the change, read the help of the new version for the words the line that installs uses, against row "The help of `uv`" of section 14. It is one change and one push, and can wait for a push you are making anyway.

## 11. What it costs

| Thing | Cost | Basis |
|---|---|---|
| Running the workflows | GBP 0 | Read: GitHub Actions is free for public repositories on standard runners. These workflows use the standard runner, `ubuntu-24.04` |
| Environments, approvals and secrets | GBP 0 | Read: on a free plan they are offered for public repositories |
| The store, under 10 GB | GBP 0 a month | Read: the first 10 GB are free each month |
| The store, above 10 GB | USD 0.015 for each GB each month. At 40 GB that is USD 0.45, about GBP 0.35 | Read. The exchange rate is assumed at USD 1.30 |
| Writing and listing files | Free up to 1 million requests a month, then USD 4.50 a million | Read. A fetch of 30 files is some hundreds of requests (estimate) |
| Reading files | Free up to 10 million requests a month, then USD 0.36 a million | Read |
| Taking files out of the store | GBP 0 | Read: no charge to read out |
| A lock on the bucket | Not known | Not read |
| A payment card at Cloudflare | Not known | Not read |
| Your time to set up | About 1 hour and a quarter, once | Estimate |
| Your time for each run | About 5 minutes: start, approve, read the result | Estimate |

What would change it:

| If | Then |
|---|---|
| The repository is made private | Runs are counted against 2,000 free minutes a month (read), and the environments' rules need a paid plan (read) |
| A workflow is moved to a larger runner | It is charged by the minute, on a public repository too (read) |
| Files are uploaded to GitHub as artifacts or caches | They are counted against GitHub's storage. The rules forbid it |

## 12. What only a first run can show

Nothing below could be tried before the repository was on GitHub. The rehearsal of section 5 shows rows 1 to 14 with nothing real at stake. Rows 1 to 4 matter most. Note every row that is not so, and have them mended together: one push, and not one for each.

| # | Not known | How the first run shows it | If it is not so |
|---|---|---|---|
| 1 | That the step "Every secret is set" never shows a value it asks the runner to hide. It should read `::add-mask::***`, or show no such line | Read that step's log in the rehearsal | Stop. The step must then ask the runner to hide nothing, and rely on `tools/public_log.py` alone |
| 2 | That one approval starts both builds | Count the approvals you are asked for | Two clicks in place of one. Nothing else changes |
| 3 | That GitHub gives the log of a job that has ended while the run is still going | The last job passes, or says `status=unreadable` | The search must move to after the run, which needs a change to the workflow |
| 4 | That the pinned commits of the two actions exist and do what their version says | The first two steps of any job pass | `ci.yml` pins the same commits, so its first run shows this too |
| 5 | That GitHub tells a run the name of the default branch | The step "The run is on the default branch" passes on `main` | It fails on `main` too, and no job is given a secret. Tell the builder |
| 6 | That each copy of the build gives its own output, `a` and `b`, and neither writes over the other | "Compare the two builds" does not say `status=missing` | The two builds become two jobs written out one after the other |
| 7 | That the runner's image holds what `uv` needs to bring Python 3.13, and that a tool run before anything is installed is given a Python that can read it | The first step of "Rules and canary", and "Install", pass | Name the Python version in the step that sets up `uv` |
| 8 | That a run started from another branch stops before any job is given a secret | Make a branch on the website, and start a run from it, once, with the rehearsal's secrets. Its first job fails, and no job waits for you. Delete the branch | Check step 6 of section 2, and tell the builder |
| 9 | That a step is left out when the item is empty, and run when it is not | In a fetch, one of "Fetch every file" and "Fetch one item" is grey | Tell the builder |
| 10 | That the two build machines give the same bytes | "Compare the two builds" | This is what the job is for |
| 11 | How long each job takes | The run's page | The estimates here are corrected |
| 12 | That the line named "Install" finds every package under the day it states. The public index must say when each file was uploaded, or the file is refused (read) | "Install" passes, in "Rules and canary" | Tell the builder. The day is moved, or the line is changed |
| 13 | That a command run in what was installed finds the pipeline, with no lockfile committed | "A planted row and a planted key" and "Build the synthetic release" pass | Tell the builder |
| 14 | That the step which checks made-up secrets accepts the four values of section 4 | "Every secret is set" passes in a build | Paste them again, letter for letter. Then tell the builder |
| 15 | That the store answers a runner, and the fetch key can list and write | "The store answers" in the first fetch with the real secrets. No code here has ever reached a real store | Tell the builder: the step shows only that it failed |
| 16 | That the lock lets a first write through, and refuses a delete | The first fetch stores its files. Then try to delete one in Cloudflare | Take the rule off, fetch, and tell the builder |
| 17 | That a publisher's host answers a runner | The first fetch of each file | The file is saved by hand, as ADR 0015 allows |
| 18 | That each address in the first list gives its file | The first fetch of each file | Save the file by hand from the right address, and put the list right in your next commit |
| 19 | That a key which may read and no more can list the store | "The store holds every file that has a receipt", in the first run of the check | Tell the builder: the step shows only that it failed |

## 13. What is not built yet

| Not built | Why | Until then |
|---|---|---|
| A run of the build of London | The workflow that builds London, keeps the release and shows its lock is built, and has never run. No bucket of releases exists: [London, from the bucket to the service](#london-from-the-bucket-to-the-service) | London is built on a machine of your own: section 29. The workflow `data-build` builds the made-up city, compares and throws away, as a rehearsal |
| The full log of a step, kept in the store | No code writes a log to a store | A failure is found on made-up data: section 9 |
| Bringing a receipt from a run into the repository | A fetch writes the receipt to the runner's disk, and the runner is thrown away. So the fetch also keeps a copy in the store. To reach the repository from there, a person brings it back, or the run shows it, or the run pushes it. The second shows more than step names, counts and hashes. The third needs a permission to write that no data workflow has. The plan's decision 2, on committing receipts in public, is also open | A person brings the receipts back and commits them: section 7. It needs a key on a machine of your own. Whether that is acceptable is yours to decide |
| Bringing the reports of a build from a run into the repository | No run may write to the repository, and a coverage report names areas, so no run may show it. The lock of a release holds no name and no figure, so a run shows it, and you commit it: [London, from the bucket to the service](#london-from-the-bucket-to-the-service) | The reports are kept beside the release, in the bucket of releases. Take the release to a machine of your own to read them: [London, from the bucket to the service](#london-from-the-bucket-to-the-service), under "Read the lock, and approve the release" |
| A hosted run that serves what was approved | To deploy needs the host's own program on a runner, which no workflow may install | You take the release and deploy it, on a machine of your own: [the guide to deployment](../deploy/README.md) |
| A build from the names a person decided | The decisions of the review desk are on a machine of a person's own, and the copy that may be committed is not committed | A hosted build makes the draft of names from the store, and every name says that it is a draft |
| Showing the shape of a fetched file in a run | The plan's fastest route to M1 has the first fetch print each file's sheet and column names. Those are not step names, counts or hashes, and where a table has no header they are a row. So a run withholds them, and no workflow runs it | `uv run python -m burro_pipeline describe` on a machine of your own that holds the reading key: section 7 |
| A check, inside a run, that the environment has a reviewer and a branch rule | GitHub gives an environment's rules to anyone who may read the repository (read), so the first job could ask and refuse to go on. It was left out because the answer's shape has not been seen, and a check that is wrong would stop every run | You watch for the wait: section 2 |
| A build from a committed lockfile | The lockfile is not committed yet: ADR 0008 says when it will be | Every build is a development build, and is never served. A run holds its packages to a day, and not to a hash: section 10 |
| A fetch of only the files the store does not hold | A fetch asks the publisher for every file it is given, stored or not | The check of section 7 names each file the store does not hold. To fetch again what failed, start a run for each item, or one for the whole list |
| A receipt written from the store, with nothing asked of the publisher again | The same. The second run of a file asks its publisher for it again, to write the receipt | Every file is fetched twice: section 7 |
| The hash of the file that was read, held in the list | A list holds no hash. So nothing but `new=0` on the line of the second run shows that the receipt is of the file that was read | Read `new=` on each line of the second run: section 7 |
| A way to give a build every edition of an earlier lock at once | A build is told an edition with `--edition ITEM=EDITION`, once for each file. The register is 33 files, so a build that repeats an earlier one is given 33 | Read `item` and `edition` of each input in the earlier `lock.json`, and give each: section 7, "Which edition a build takes" |
| The step `seal` for more than one list | `seal` takes one list, and refuses a folder that holds a receipt of another. `preview` takes several, and seals as it starts | Build with `preview`, which writes the lock beside the release |
| A record of a correction that a step reads | A receipt is put right by hand, and the record is the history of the repository. No step checks it | Section 7, "Put a receipt right" |
| Routing London | The engine that routes a real timetable needs Java, and packages that no run may install yet. The timetables of Transport for London were fetched on 2026-09-24 and have their receipt, and none has been converted. [The travel design](design/london-data-travel.md), section 18, lists what stands in the way | The workflow `data-travel` routes the made-up town, with the router that is for tests |
| A workflow for research with a model | A later milestone | |
| Showing the kind of error a step failed with | The rule is step names, counts and hashes only. The name of an error and the line of code it came from hold no data, and would make a failure far quicker to find. The fetch command already prints the kind of a fault, and a run withholds it | Yours to decide |

## 14. What was read

Read on 2026-09-23 through a reader that summarises. Check the wording in a browser before relying on it.

| Page | What it says |
|---|---|
| GitHub Docs, workflow syntax | `workflow_dispatch` "only receives events when the workflow file is on the default branch". `permissions: {}` turns every permission off. The list of permissions |
| GitHub Docs, events that trigger workflows | For a run started by hand, the branch is the one chosen when it was started |
| GitHub Docs, manually running a workflow | The steps of section 6. "Write access to the repository is required" |
| GitHub Docs, managing environments | "Users with GitHub Free plans can only configure environments for public repositories." Up to 6 reviewers, of whom one must approve. "Prevent self-review". Secrets of an environment reach a job only after its rules pass. "Running a workflow that references an environment that does not exist will create an environment with the referenced name", with no rules and no secrets |
| GitHub Docs, REST API, environments | "Anyone with read access to the repository can use this endpoint" to get an environment and its rules |
| GitHub Docs, variables | `RUNNER_DEBUG` "is set only if debug logging is enabled, and always has the value of 1". A run's number "does not change if you re-run the workflow run" |
| GitHub Docs, reviewing deployments | "Review deployments", "Approve and deploy". A reviewer selects "the job environment(s) to approve or reject" |
| GitHub Docs, workflow commands | `::add-mask::` hides a value in the log. A run's summary hides secrets too |
| GitHub Docs, secure use | A secret is hidden only where its exact value is printed. A value made from a secret must be registered to be hidden. An action pinned to a full commit is the only kind that cannot change |
| GitHub Docs, REST API, workflow jobs | The addresses for the jobs of a run and the log of a job. The log is a redirect that lasts one minute. Whether it is given while a run is going is not said |
| GitHub Docs, billing for Actions | Free for public repositories on standard runners. Larger runners are always charged. 2,000 minutes a month for private repositories on the free plan |
| The `setup-uv` action's page | Its cache is on by default on hosted runners. These workflows turn it off |
| GitHub Docs, deployments and environments | The three choices for deployment branches. "If the environment requires approval, a job cannot access environment secrets until one of the required reviewers approves it." By default administrators can bypass the rules |
| GitHub Docs, enabling debug logging | It is turned on by a secret or a variable, or by anyone who may run a workflow, for one run. It adds to the log. Whether secrets stay hidden is not said |
| Cloudflare R2, API tokens | The four permissions, and what each allows. "Object Read & Write" allows "the ability to read, write, and list objects in specific buckets". The page does not name deleting a file. A token is held to "a set of buckets". The secret is shown once. "To issue short-lived, scoped credentials derived from an API token, use temporary credentials" |
| Cloudflare R2, bucket locks | "Bucket locks prevent the deletion and overwriting of objects in an R2 bucket for a specified period — or indefinitely." "Rules without prefix apply to all objects in the bucket." A rule is for a number of days, until a date, or indefinitely. It is made in the bucket's settings, under "Add rule". Up to 1,000 rules. What is answered to a delete is not said |
| Cloudflare R2, the S3 operations it offers | Deleting a file is offered. Writing a file only if none is there is offered |
| Cloudflare R2, pricing | The prices of section 11 |
| Cloudflare R2, create buckets | The rule for a bucket's name. "Bucket names and buckets are not public by default" |
| The help of `uv` at the version the workflows pin, 0.12.17 | `--package`: "The workspace's environment (`.venv`) is updated to reflect the subset of dependencies declared by the specified workspace member packages." `--no-dev`: "Disable the development dependency group." `--exclude-newer`: "Limit candidate packages to those that were uploaded prior to the given date. The date is compared against the upload time of each individual distribution artifact". `--no-sync`: "Avoid syncing the virtual environment. Implies `--frozen`". `--no-project`: "If a virtual environment is active or found in a current or parent directory, it will be used as if there was no project or workspace" |
| uv's documentation, resolution | "The package index must support the `upload-time` field". "If the field is not present for a given distribution, the distribution will be treated as unavailable". Whether the day holds what a build needs is not said |
| The help of `uv sync`, at the same version, on what is read beside the line | `--exclude-newer-package`: "Limit candidate packages for specific packages to those that were uploaded prior to the given date." `--config-file`: "The path to a `uv.toml` file to use for configuration", also read from `UV_CONFIG_FILE`. `--no-config`: "Normally, configuration files are discovered in the current directory, parent directories, or user configuration directories." Most settings of the line name a variable they are also read from, such as `UV_EXCLUDE_NEWER`, `UV_INDEX` and `UV_FIND_LINKS` |

Tried, with no network, on made-up packages, with `uv` at the version the workflows pin:

| Tried | What it showed |
|---|---|
| The line named "Install", for one package of a made-up workspace | That package alone was installed |
| A command run with `--no-sync`, and one with `--no-project`, after it, with no lockfile | Each ran in what was installed. Nothing more was installed |
| A plain `uv run` after it | It installed the rest of the workspace. That is what the check now refuses |
| The line with a day before any build tool was published | The build was refused: the day holds what a build needs too |
| The line where no upload day was known for a file | The file was refused |

Not tried: the line against the public index. That is row 12 of section 12. Not tried for this guide: that a settings file, or a setting given to a step, changes what the line brings. The check refuses each on what the installer's help says of it.

Not read, and written from memory: that Cloudflare asks for a payment card, the names of the buttons on Cloudflare's pages, that a run waits 30 days for approval, that the logs of a run can be deleted from its page, that a run can be run again from its page, that a branch can be made on the website, and that to delete is a kind of write in the protocol the store speaks.

## London, from the bucket to the service

For the founder. Written 2026-09-25. It has no number: it is part of the guide to hosted builds, which ends here, and the numbered sections that follow are the record of each preview. It applies [ADR 0030](adr/0030-a-release-is-kept-approved-by-its-lock-and-carried-in-the-image.md).

**Nothing here has run on a host.** The workflow has never run, and no bucket of releases exists. Every step of it was driven on a machine of a developer's own, with a folder standing in for each bucket: the part "What was tried" says what that showed. What only a first run can show is listed under "What only a first run can show". Every time below is an estimate.

Until now London was built on a machine of a developer's own. From here a hosted run builds it from the store in the bucket, and from nothing else. Once the store is in the bucket, the repository and the two buckets are all that a release needs.

A change you keep at the panel of the review desk is served once it is published with `make desk-publish`, committed to `main`, built by a hosted run and approved with its lock. Both builds of a run are given the one place the desk publishes your file to, `gazetteer/london/decisions/changes/r1.jsonl`: where the repository tracks a file there the build applies it and its lock names it by its hash, and where it tracks none the run builds as it did, byte for byte.

| Question | Answer |
|---|---|
| What you make, once | One bucket at the store, for releases. Three keys. One environment on GitHub, `data-london`, with eight secrets |
| What a run asks of you | Two inputs when you start it, and two approvals: one before each build is given the key |
| What a run keeps | The release, in the bucket of releases, and only where two builds of it are the same, byte for byte |
| What a run shows | Step names, counts and hashes, and the lock of the release on its summary page. No figure, and no name of a place |
| What makes a release one that is served | Its lock, committed to `main` under `data/approved/`. Only you commit one |
| What is served with no lock | The made-up city, as today |
| How long it takes | About 40 minutes to set up, once. About an hour and a half for a run, of which 5 minutes are yours |

### What you do, in order

| # | Where | Do this | What you see when all is well |
|---|---|---|---|
| 1 | Cloudflare | Make the bucket of releases, and its lock | A second bucket, with public access off and one rule |
| 2 | Cloudflare | Make the three keys: build, keep and take | Three tokens. Each secret is shown once |
| 3 | GitHub | Make the environment `data-london`, as section 2 says, with you as its reviewer and `main` as its only branch | The environment, with its two rules |
| 4 | GitHub | Store its eight secrets | Eight names under "Environment secrets" |
| 5 | GitHub | Start the workflow, with the id of the release and the time it is said to be built | The run. Its first job starts at once |
| 6 | GitHub | Approve the first build. When it has ended, approve the second | "Build a" runs, then "Build b, and keep what two builds agree on" |
| 7 | GitHub | Read the run | Every job green. The last line of "Keep the release" reads `status=ok` |
| 8 | GitHub | Read the lock on the run's summary page | What the release holds, what was left out, and the hash of every file |
| 9 | A machine of your own | Look at the release before you approve it, if you wish | London on your own screen, as section 15 shows a preview |
| 10 | A working copy of `main` | Save the lock under `data/approved/`, check it, and commit it, by a pull request or a push of your own | `step=lock status=ok`, with the hash the run showed |
| 11 | A machine of your own | Take the release and deploy it | [The guide to deployment](../deploy/README.md), "Serving a release of London" |

Steps 1 to 4 are done once. Steps 5 to 11 are done for each release.

### 1. The bucket of releases

About 10 minutes. It is made as the bucket of publishers' files was: section 3, "The bucket".

1. In Cloudflare, open **R2**, and create a bucket.
2. Name it with a part nobody could guess, such as `burro-releases-` and eight random letters and digits. Its name is a secret, as the other's is.
3. Choose the location the first bucket has. Set no jurisdiction unless the first bucket has one: the address of both is then the same.
4. Leave public access off. Never turn on the public address of this bucket, and never give it a domain: a release holds real figures of real places.
5. Add one lock rule, as section 3 says: name it `releases`, give it the prefix `releases/`, and keep files locked for 90 days.

It is a bucket of its own because a key is held to a bucket, and to nothing finer (read). In a folder of the first bucket, the key that keeps a release could write a publisher's file.

| | |
|---|---|
| What is under `releases/` | Every file of every release that was kept, under the folder it was built in and then its own name |
| What is never there | A publisher's file, and a receipt |
| What the lock changes for a run | Nothing. A run writes a file only where none is, and never deletes |
| What the lock stops | For 90 days: a key that was seen, or a workflow that was changed, from deleting a release or putting another in its place |
| What the lock is not relied on for | That what is served is what you approved. The lock you commit holds the hash of every file, and a file that differs is refused when it is taken and again when the image is built |
| How much it holds | About 90 MB for each release |

### 2. The three keys

About 15 minutes. Each is made as section 3, "The keys", says: **R2**, then **Manage API tokens**, create a token, pick the permission, pick **Apply to specific buckets only**, and pick the one bucket.

| Key | Permission at Cloudflare | Bucket | It may | It may not | Kept |
|---|---|---|---|---|---|
| Build | Object Read only | The bucket of publishers' files | Read and list the files a build is made from | Write or delete anything. Touch the bucket of releases | In the environment `data-london` |
| Keep | Object Read & Write | The bucket of releases | Read, write and list releases | Touch a publisher's file or a receipt. Make, change or delete a bucket. Change a lock | In the environment `data-london` |
| Take | Object Read only | The bucket of releases | Read and list releases | Write or delete anything. Touch a publisher's file | In your password manager, for the machine you deploy from. Never on GitHub |

Put the id and the secret of each in your password manager before you close the page. Make each a token of its own: a key that is shared by two jobs cannot be rotated for one of them.

### 3. The environment, and its eight secrets

About 15 minutes. Make the environment as section 2 says: required reviewers, you alone. Prevent self-review off. Administrators may not bypass. Deployment branches, `main` only.

| Name | What it is | In `data-london` |
|---|---|---|
| `BURRO_STORE_ENDPOINT` | The address Cloudflare shows for S3 clients, whole, beginning `https://` | The real one |
| `BURRO_STORE_BUCKET` | The name of the bucket of publishers' files | The real one |
| `BURRO_STORE_KEY_ID` | The id of a key | The real one, of the build key |
| `BURRO_STORE_SECRET` | The secret of a key | The real one, of the build key |
| `BURRO_RELEASES_ENDPOINT` | The address Cloudflare shows for S3 clients. It is the address above, where both buckets are in one account and neither has a jurisdiction | The real one |
| `BURRO_RELEASES_BUCKET` | The name of the bucket of releases | The real one |
| `BURRO_RELEASES_KEY_ID` | The id of a key | The real one, of the keep key |
| `BURRO_RELEASES_SECRET` | The secret of a key | The real one, of the keep key |
| `BURRO_FETCH_CONTACT` | | No |

Never store the fetch key here, and never the take key. A build that holds the fetch key could write a publisher's file.

Which step is given which key is written in the workflow, and the rules check holds it there:

| Step | It is given | And never |
|---|---|---|
| "The store answers", "Draft the names of the areas", "Build London" | The build key | The keep key |
| "Check the release", "Hash what was built", "Compare the two builds", "Show the lock of the release" | Nothing | Any key |
| "Keep the release", in the second build alone | The keep key | The build key |

The first build is given no key that writes. Not even its step that checks the secrets is.

### 4. Start a build of London

About an hour and a half, of which 5 minutes are yours.

1. Open **Actions**, choose **data-london**, and press **Run workflow**. Leave the branch as `main`.
2. Type the id the release is built under: `lon-`, the day, and a number of two digits, as `lon-2026-10-02-01`. Use an id that no build was kept under. A release is never written over, so a second build of one day takes the next number.
3. Type the time the build is said to be made, in UTC, as `2026-10-02T09:00:00Z`. Give the hour of the last commit on `main`, and never a time that has not come: the service serves it as the time the release was built. It is typed and never read from a clock, so that two builds give the same bytes.
4. Press the green **Run workflow**. Open the run. "Rules and canary" starts at once.
5. When it has passed the run says it is waiting. Press **Review deployments**, tick `data-london`, and press **Approve and deploy**. "Build a" starts.
6. When "Build a" has ended the run waits again. Approve it again. "Build b, and keep what two builds agree on" starts.
7. When the run has ended, open its summary page. The lock is at the foot of it.

Before you approve, look at the commit the run was started from, as section 2 says under "Who may approve". This run is given a key that writes.

| Job | Waits for you | Is given | What it does |
|---|---|---|---|
| Rules and canary | No | Nothing | As in every data workflow |
| Build a | Yes | The build key | Copies every file out of the store. Drafts the names of the areas. Builds London. Checks the release against the receipts that are committed. Hashes every file it built, and hands the hashes on |
| Build b, and keep what two builds agree on | Yes | The build key, and for one step the keep key | Builds again on a second runner, the same way. Holds what it built to the hashes of the first build. Keeps the release. Shows its lock |
| Search what the run made public | No | The run's own token, to read the logs | As in every data workflow |

What is built is what a build on a machine of your own makes: section 29. Two things are no longer handed to it:

| | How it was | How it is |
|---|---|---|
| The names the areas bear | A draft was made first, on a machine of a developer's own, and its folder was given to the build | The run makes the draft from the store, with the step `draft`, and gives the build its folder. Every name still says that it is a draft |
| Household income | It was read by the build, from the store | The same. It is written beside the release, and kept with it |

Once names are decided at the review desk, a build is given what the desk decided. Until those decisions are committed, a hosted run cannot read them: the part "What is not built" says so.

### 5. What a run prints

Each line is one the list of section 8 allows. The counts below are those of a build on a machine of a developer's own, from the thirteen lists there are. `missing` counts the files of a list that have no receipt: a build goes on without them, and the measures that rest on them are left out.

| Step | It prints | What a green step means |
|---|---|---|
| Every secret is set | `step=secrets set=4 missing=0` in the first build, and `set=8` in the second | Each secret is stored and was pasted whole |
| The store answers | `step=store kind=object_store`, then `step=store status=ok files=89 bytes=5584175799` | The address and the build key are right |
| Draft the names of the areas | `step=store status=ok kind=object_store files=86 bytes=...`, then `step=names status=ok exit=0 withheld=1 seconds=...` | Every file that has a receipt was copied out of the store and is the file of its receipt. The draft was made. Its own line of counts is withheld |
| Build London | `step=seal status=ok release=lon-2026-10-02-01 inputs=89 missing=4 own_edition=41 named=0 passed_over=0 development=1 lock_sha256=...`, then a line of `step=cells` and of `step=names`, a line of `step=derive` for each measure, and a line each of `step=cost`, `step=places`, `step=assemble`, `step=check`, `step=income` and `step=report` | The release was written on the runner. `findings=0` on the line of `step=check` says that every fact has evidence behind it |
| Check the release | `step=check status=ok exit=0 withheld=2 seconds=...` | `burro-release check` accepts the release and the folder of household income, against the receipts that are committed. What it says in words is withheld |
| Hash what was built | `step=lock status=ok copy=a release=lon-2026-10-02-01 files=21 bytes=... areas=1002 measures=98 vibes=14 sha256=...` | Every file was hashed. `sha256` is the hash of what the lock says |
| Compare the two builds | `step=compare status=ok files=21 differing=0 sha256=...` | The second build is the first, byte for byte. The hash is the one "Hash what was built" gave |
| Keep the release | `step=keep kind=object_store`, then `step=keep status=ok release=lon-2026-10-02-01 files=21 bytes=... new=21 same=0` | Every file of the release is in the bucket of releases |
| Show the lock of the release | `step=lock status=ok release=lon-2026-10-02-01 files=21 sha256=...` | The lock is on the run's summary page |

A line of `step=derive status=skipped` names a measure that was worked out and left out, and the rule that kept it out. It is no fault. The lock lists each.

### 6. Read the lock, and approve the release

The lock is the last thing on the run's summary page: a table, and then a block that begins `{` and ends `}`. **To approve the release is to commit that block.** Until you do, the release is kept and served nowhere.

Read these before you approve:

| In the lock | Read it for |
|---|---|
| `release_id`, `commit`, `built_at` | That it is the release you started, built from the commit you looked at |
| `preview` and `development` | Both read `true` today. A preview is a release that is not finished. A development build is one whose packages were held to a day and not to a hash: ADR 0015 says that such a build is never served to the public. To commit the lock is to say that this release may be carried by an image. It is not to say that the public may be shown it |
| `holds` | How many areas, measures and vibes it holds, against the build before |
| `left_out` | Each measure that was worked out and left out, and the rule. A measure that is here and was not before is a measure that people will no longer find |
| `files` | Nothing. It is what the image is held to |

To look at the release itself before you approve it, take it to a machine of your own with the take key, from a copy of the lock that is not yet committed. [The guide to deployment](../deploy/README.md) says how the step is given its key.

```
uv run python -m burro_pipeline take --release lon-2026-10-02-01 --approved FOLDER --out data/releases/look
```

`FOLDER` is any folder outside the repository that holds the lock, named `lon-2026-10-02-01.json`. The step holds every file to the lock, so what you look at is what the run built. Then open it as section 15 says, from step 6, with `data/releases/look/lon-2026-10-02-01` as the folder of the release. The coverage report is beside it, in the folder that ends `-build`. Remove `data/releases/look` when you have looked.

To approve, in a working copy of `main`:

1. Press the copy button of the block on the summary page, and save what it holds as `data/approved/lon-2026-10-02-01.json`. The name of the file is the id of the release.
2. Run `uv run --no-project python tools/release_lock.py read data/approved/lon-2026-10-02-01.json`. It prints one line, which begins `step=lock status=ok`. Its `sha256` must be the one the step "Show the lock of the release" printed. If it is not, what you saved is not what the run showed: copy it again.
3. Run `make ci`.
4. Commit the file, and nothing else, with a message that names the release. Bring it into `main` by a pull request or a push of your own.

A lock is never changed once it is committed. A release that is wrong is built again under a new id, and has a lock of its own. To stop a release from being served again, take its lock out with `git rm`, and commit that.

### 7. Serve it

[The guide to deployment](../deploy/README.md), "Serving a release of London", says how the release is taken and carried by the image, what to look at once it is served, and how to go back to the release before.

### When a run of the build fails

Open the run, then the job with the red cross, then the step with the red cross. Section 9 says what to do about a step that every data workflow has. These are the steps of this one.

| The step | The log says | It means | Do this |
|---|---|---|---|
| Every secret is set | `error: BURRO_... is not set`, and `step=secrets status=missing` | A secret of the environment is missing or was pasted badly | Paste it again: "The environment, and its eight secrets" |
| The store answers | `step=store status=failed exit=2` | The store did not answer, or refused the build key | Check the address, the name of the bucket and the key, in that order |
| Draft the names of the areas | `step=areas-draft status=refused file_is_in_the_vault=1`, and then `step=names status=failed exit=2` | A file that has a receipt is not in the store, or is not the file its receipt names | Fetch the file again, or hand it over with the step `by-hand`: section 7. Never change a file in the store |
| Build London | `step=assemble status=refused file_is_in_the_vault=1`, with a `file_id` | The same, of a file of the build | The same. The receipt of that file is named for the `file_id` |
| Build London | `step=assemble status=unreadable` | An input was typed badly, or the list of the build cannot be read. Or the file of changes that was published cannot be built on: a line of it breaks a rule, or was decided of something that has since moved | Read what you typed: the id is `lon-`, a day and two digits, and the time ends `Z`. Start a new run. If what you typed is right, build on a machine of your own with `--changes` to read which line it is, and take the line back at the panel |
| Build London | `step=assemble status=failed why=8` | The store did not answer, or refused the build key, after the step "The store answers" had its answer. The number is the one a line of fetch gives a store that fails | Check the address, the name of the bucket and the key, in that order. Then run the failed job again |
| Build London | `step=assemble status=refused`, with the name of a rule | A file is not what the step was written to read, or the release breaks a rule | Tell the builder the rule. Build it on a machine of your own to read the words: section 15 |
| Build London | `step=check status=failed`, with `findings=` and a number | A fact of the release has no evidence behind it. Nothing was written | Tell the builder the rules that the line counts |
| Check the release | `step=check status=failed exit=1`, or `exit=2` | `burro-release check` refuses the release, or a receipt in its evidence is not the one that is committed | Bring the receipts back and commit them, if the store holds a receipt that the repository lacks: section 7. Otherwise tell the builder |
| Compare the two builds | `step=compare status=differs`, with `file=` on a line for each file, and `differing=` | The two runners built different bytes. Nothing was kept | Tell the builder which files. The release is not used |
| Compare the two builds | `step=compare status=differs`, with `wrong=` and a number | The two builds are of two commits, or of two times. Nothing was kept | Start a new run. Approve both builds of one run, and start no run between them |
| Compare the two builds | `step=compare status=missing` | The first build handed no hashes on | Look at "Hash what was built" in the first build |
| Keep the release | `step=keep status=refused`, with `differs=` and a number | A build was kept under this id before, and it is not this one. Nothing was kept, and what was there is as it was | Start a new run under the next number |
| Keep the release | `step=keep status=failed exit=2` | The bucket of releases did not answer, or refused the keep key | Check the three values of the bucket of releases. Then run the failed job again: a file that is kept already is left as it is |
| Any step | `secrets=1` or more | A step printed a secret. The line was withheld | Rotate that key: section 10. Tell the builder |

A run that ends red has kept nothing, unless the step "Keep the release" is the one that failed. What such a run left in the bucket is served nowhere: no lock was shown, so none can be committed.

### What only a first run can show

| # | Not known | How the first run shows it | If it is not so |
|---|---|---|---|
| 1 | That the second build waits for a second approval, and that the first build's hashes reach it | The run waits twice. "Compare the two builds" does not say `status=missing` | Tell the builder |
| 2 | That a runner has the disk a build needs. The copies of the store's files took 8.5 GB on a machine of a developer's own, and what a build wrote 170 MB. GitHub gives a runner of a public repository 14 GB of storage, and does not say how much of it is free (read) | "Draft the names of the areas" and "Build London" pass | Tell the builder: a step that fails for want of disk shows only that it failed |
| 3 | That a runner has the memory a build needs. On a machine of a developer's own the build took 3.1 GB at its peak, the draft 1.7 GB and the check of the release 0.9 GB. GitHub gives a runner of a public repository 16 GB (read) | "Build London" passes | The same |
| 4 | How long a build takes on a runner. On a machine of a developer's own, with 16 cores, the draft took 2 to 5 minutes, the build 9 to 12 and the check of the release 2 to 3, over five builds. A runner has 4 cores, and copies the files over a network first | The run's page | The limit of each job is two hours. Tell the builder if a build comes near it |
| 5 | That two runners give the same bytes. Two builds on one machine do | "Compare the two builds" | This is what the step is for |
| 6 | That a key which may read and no more can list the store and copy a file out | "The store answers", and the first line of "Draft the names of the areas" | Check the key's permission and its bucket |
| 7 | That the bucket of releases takes a file that is sent only if none is there, and answers as the code expects where one is. Cloudflare lists the condition as one it keeps (read), and not what it answers | "Keep the release", in the first run and in a run that is started again | Tell the builder: the step shows only that it failed |
| 8 | That the summary page shows the lock whole, with a button to copy it | The run's summary page | Copy the block by hand. The step of "To approve" that reads the lock tells a bad copy |
| 9 | That GitHub hands a job's output on where it holds many hashes. If a value a run hides stood in it, the output would be dropped | "Compare the two builds" does not say `status=missing` | Tell the builder |

### What was tried

On 2026-09-25, on a machine of a developer's own, with the store as a folder and a second folder standing in for the bucket of releases. No step reached a network, and the step that checks the four secrets was left out, there being none. It was done twice, from two commits, and showed the same each time. Nothing that was built is committed.

| Tried | What it showed |
|---|---|
| The commands of the workflow, word for word, as the first build and as the second, each in a folder of its own, from one commit with nothing changed | Both built. The two releases are the same bytes: 21 files of 88,630,949 bytes, 1,002 areas, 98 measures and 14 vibes, and one lock. `diff` found no byte that differs, in the releases or in the two drafts of names |
| A third build, by the path a step takes when its store is a bucket: the folder was handed to each step as a store that is reached over a network, which answers only while a socket may be made | The draft asked the store for 86 files before it read one, and for none after. The build that followed found the copies and asked for none. What it built is the same bytes as the other two |
| `burro-release check`, on each build, against the receipts that are committed, with the folder of household income | It accepted each |
| "Compare the two builds", "Keep the release" and "Show the lock of the release" | `differing=0`. 21 files kept, `new=21`. The lock on the summary page is 4,486 bytes, and the output of the first job 3,530 |
| "Keep the release" once more, as a failed job that is run again would | `new=0` and `same=21`. Nothing was written twice |
| "Keep the release", where a build of another commit was kept under the same id | It was refused, with `differs=3`, and ended with 1. What was kept before was as it was, byte for byte. The three files are the three that record the commit |
| Everything the three builds printed, the output of the job, the summary page and the lock, read for each of the 3,316 names the release holds of an area, a borough or a place to reach, and for each of its 20,718 figures that have a fraction or five digits or more | None is there. No number with a fraction is printed but how many seconds a step took. The same reading finds a name and a figure that are planted |
| The lock, cut out of the summary page and saved as a person would save it, and then the step `take` with it | It reads as the lock the run showed. The release that was taken is the release that was built, byte for byte |
| The same, with one byte of one file changed in a copy of what was kept | `take` said `status=differs`, ended with 1, and left no folder |
| The same, with no lock that names the release | `take` said `status=missing`, and ended with 1 |
| `take` with no lock at all and no release named | It took the made-up city: 11 files, which are the files that are committed |
| `take` with a lock approved and no release named | It was refused, and ended with 2 |
| What the image's own stage does, with no image built: on the release that was taken, on the same with one byte changed after it was taken, on a release no lock names, and on another build of London under the id the lock names | It accepted the first, and refused each of the others by the name of its file |
| The service, loaded with no socket on the release that was taken, and asked sixteen things | Every answer said `synthetic: false` and `preview: true`. It took 374 MB once loaded and 381 MB at its peak |

Not tried: anything on GitHub, at Cloudflare or at the host of the service. No bucket was reached and no image was built.

### What is not built

| Not built | Why | Until then |
|---|---|---|
| A build from the names a person decided | The decisions of the review desk are in a folder of a machine of a person's own, and the copy that may be committed is not committed | A hosted build bears the names of the draft, and says of each that it is a draft |
| A hosted run that takes a release and deploys the image | It needs the host's own program on a runner, which no workflow may install | You take the release and deploy it, on a machine of your own: the guide to deployment |
| A build of record | The package lockfile is not committed: ADR 0008 | Every hosted build is a development build. Its lock says so |
| A way to remove from the bucket a release that was never approved | No key of a workflow may delete | It stays, and is served nowhere. Remove it by hand in Cloudflare, with the rule off, as section 3 says of a file |
| The coverage report, shown to you by the run | It names areas, so no run may show it | It is kept beside the release. Take the release to read it: "Read the lock, and approve the release" |

### What was read

Read on 2026-09-25 through a reader that summarises. Check the wording in a browser before relying on it.

| Page | What it says |
|---|---|
| Cloudflare R2, API tokens | The four permissions. "Object Read only" allows "the ability to read and list objects in specific buckets", and "Object Read & Write" "the ability to read, write, and list objects in specific buckets". The page names no way to hold a token to a prefix, a folder or an object, and does not say whether a token that may write may delete. "You will not be able to access your Secret Access Key again after this step" |
| Cloudflare R2, temporary credentials | A temporary credential can be held to "a single bucket" and "optionally to specific paths within the bucket", by prefixes or by objects. It is "derived from an existing R2 API token", and "cannot exceed the permissions of its parent token". How long one may last is not said |
| Cloudflare R2, bucket locks | As section 14 has it. A rule may be given a prefix. Whether a lock stops a new file under a new name is not said |
| Cloudflare R2, S3 API compatibility | `PutObject`, `GetObject`, `HeadObject` and `ListObjectsV2` are listed as implemented. `PutObject` is listed with the conditional operation `If-None-Match`, which is how a file is sent only where none is. What R2 answers where a file is there is not said, and no header of a checksum is named |
| GitHub Docs, deployments and environments | "Use required reviewers to require a specific person or team to approve workflow jobs that reference the environment." "If the environment requires approval, a job cannot access environment secrets until one of the required reviewers approves it." Whether one approval covers two jobs that run one after the other is not said |
| GitHub Docs, workflow commands | "Job summaries support GitHub flavored Markdown." A step's summary is at most 1 MiB. "Summaries automatically mask any secrets that might have been added accidentally" |
| GitHub Docs, workflow syntax | An input of a run started by hand is one of `boolean`, `choice`, `number`, `environment` or `string`. No more than 25 inputs |
| GitHub Docs, GitHub-hosted runners | A standard runner of a public repository, under the label `ubuntu-24.04`, has 4 processors, 16 GB of memory and 14 GB of storage. How much of the storage is free is not said |

Not read, and written from memory: that a job's output may hold up to 1 MB, that GitHub drops an output in which it finds a secret, and that a code block on a summary page has a button to copy it.

## 15. The first preview, on a machine of your own

This is a development build. It is for your eyes, and is never served to the public. It needs no key, no push and no hosted run. It needs the store of fetched files as a folder, and the receipts in `data/receipts/`.

What you get: every part of Greater London as one of the statistics office's 1,002 areas, each under the office's own label, with each measure that could be built and its sources. No journey, no cost, no station and no name of a neighbourhood. Of the vibes it places an area on one, Homes: section 17. Every page says that it is a preview.

From a clean start, in a working copy of the branch that holds this guide, with everything committed:

| # | Where | Run | It takes |
|---|---|---|---|
| 0 | Anywhere | Stop whatever listens on ports 8000 and 3000. `lsof -nP -iTCP:8000 -iTCP:3000 -sTCP:LISTEN` lists it, and `kill` with the number under `PID` stops it | |
| 1 | The top of the repository | `make setup` | A minute |
| 2 | The same | `make web-setup` | A minute |
| 3 | The same | `export BURRO_STORE_FOLDER=` and the folder that is the store: the one that holds `raw/` and `receipts/` | |
| 4 | The same | `make preview ARGS="--release-id lon-2026-09-24-01 --built-at 2026-09-24T09:00:00Z --out data/releases"` | 10 seconds |
| 5 | The same | `uv run burro-release check data/releases/lon-2026-09-24-01` | Two seconds |
| 6 | A first terminal, at the top of the repository | `BURRO_RELEASE_DIR=data/releases/lon-2026-09-24-01 make api` | It stays running |
| 7 | A second terminal, in `apps/web` | `NEXT_PUBLIC_BURRO_API_URL=http://127.0.0.1:8000 npm run build` | Under a minute. It writes about 4 GB under `apps/web/.next` |
| 8 | The same | `NEXT_PUBLIC_BURRO_API_URL=http://127.0.0.1:8000 npx next start -H 127.0.0.1 -p 3000` | It stays running |
| 9 | A browser | Open `http://localhost:3000` | |

Step 0 matters. If a service on the made-up release is still listening on port 8000, step 6 cannot listen, and step 7 builds the website on the made-up release without saying so.

What each step should show:

| # | You should see |
|---|---|
| 4 | One line for each part of the work. Four lines of `step=derive` read `status=ok` and six read `status=skipped`, each with the rule that kept the measure out: `measure_is_as_core_says=1` for transport noise, and `input_has_one_receipt=1` for green cover, the nearest park, pubs and bars, places to eat and drink and water close by, whose files are in another list. The last line starts `step=report status=ok`. Two folders are written: the release, and `lon-2026-09-24-01-build` beside it with the lock, the evidence, the hashes of the build, the coverage report and `build.json` |
| 5 | `lon-2026-09-24-01: 1002 areas (1002 rankable), 4 measures, 0 destinations, 0 places, 0 stations, real, a preview, with evidence behind every fact` |
| 6 | One line that holds `"preview":true` and `"synthetic":false`. If it holds `"synthetic":true`, the service is on the made-up release: it was started with no release named |
| 9 | A banner that says the release is a preview, and no banner that says the data is made up. The map draws London. Under Settings, turn a measure on: every area is ranked, and each card gives a figure with its source |

If a step stops:

| What you see | Why | Do this |
|---|---|---|
| `step=assemble status=refused tree_has_no_changes=1` | The lock names the code by its commit, and the working copy holds changes that are not committed | Commit them, or put them aside, and run step 4 again |
| `error: the folder lon-2026-09-23-01 is there already` | A release is never written over | Remove both folders under `data/releases/`, or build under a new id |
| `step=assemble status=refused file_is_in_the_vault=1` | A file in the store is not the file its receipt names | Fetch the file again. Never change a file in the store |
| `step=assemble status=refused input_has_one_receipt=1` | A file the geography needs has no receipt in `data/receipts/` | Bring the receipts back: section 7 |
| The website shows the banner for made-up data, or every page says "This page cannot be shown" | It was built with no API to read, from the recorded answers, or on a service that held the made-up release. A page built on made-up data shows no real figure | Start the API on the preview first, see that step 6 says `"synthetic":false`, and build again with `NEXT_PUBLIC_BURRO_API_URL` set |
| `error: the release could not be loaded: ... hashes.json [real_release_has_its_build]` | A release that is not made up is served only with the folder `ID-build` beside it, which holds its evidence, its lock and the hashes of the build | Keep the two folders side by side. If one was moved or copied alone, bring the other with it |
| `[build_is_as_it_was_written]` | A file of the release, its evidence or its lock was changed after the build | Never change a file of either folder. Build again under a new id |
| `--out is inside the repository` | What the step writes is made from publishers' files, and is never committed | Give `--out data/releases`, or a folder outside the repository |
| Searching says that Burro could not be reached | The API is not running, or the website is open at an address the API does not allow | The API allows `http://localhost:3000` and no other, unless it was started with another in its setting for the origins it allows: `services/api/AGENTS.md` names the setting |

What to know before you look:

- `-H 127.0.0.1` keeps the website to your own machine. Without it `next start` answers every machine on the network you are on.
- Use `npm run build` and `next start`. `npm run dev` rewrites `apps/web/AGENTS.md`.
- A sentence typed into the box is read by the rules, which know few words for what this release measures. Use Settings to rank. A budget, a journey or a vibe other than Houses or flats leaves every area unranked or is refused: the release has nothing to test one against.
- Noise is not in it until the label of the measure in core says residents and not homes. File 8 of the Indices of Deprivation has its receipt, and the receipt is committed.
- To build it again after a change, give the release a new id, or remove the two folders first. Built twice from the same files and the same commit, the two folders hold the same bytes.
- Homes built before 1919 has no figure in 23 areas. The publisher counts 1 to 8 old homes in each and writes a dash, so the share is not nought and is not known. The map shows a gap there, and the coverage report lists each.

## 16. The second preview

It is the first preview, built again with the files of a second list. Five more measures are worked out from them, and each is left out of the release, as transport noise is. The two that count places to eat and drink were added after the second build, and [the page on the food register](research/data/food-register.md) says what they rest on. [The page on the second build](research/data/m2-second-build.md) says what it holds, what was left out of it and why, and what to look at first.

It takes the place of `lon-2026-09-24-02`, which two checks found wanting. That release carried green cover under a name that reads wider than the figure, and scored the tag Leafy by a recipe the design of the vibes has withdrawn.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-24-03 --built-at 2026-09-24T01:00:00Z --out data/releases --list m1 --list m2-places"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-24-03 --receipts data/receipts` |
| 6 | The same, with `lon-2026-09-24-03` where section 15 has `lon-2026-09-24-01` |

What to know before you look:

- `--list` is given once for each list the build takes, in any order. With none, the step takes `m1` alone. A measure whose file is in no list of the build is left out: `step=derive status=skipped feature=green_cover`, with `input_has_one_receipt=1`.
- A build holds what a home sells for where a list it takes names the workbook of median prices, as `m2-living` does: give `--list m2-living` too. The line `step=cost status=ok` counts the areas and the rows, and prints no price. The line `step=cost status=skipped` names the rule that left the cost out, and the build goes on: `input_has_one_receipt` where the workbook has no receipt for the use the list names, and `input_is_allowed` where the list names it to validate against. `build.json` counts the areas with a figure for each kind of home. A build of that day held no rent: since 2026-09-25 one holds what a home lets for where a list it takes names the workbook of rents, as `m2-living` does, and section 32 says what it prints. [ADR 0021](adr/0021-a-price-is-shown-as-the-publisher-gives-it.md) says what is carried, and what waits on a decision.
- No build of London holds a price yet. One file is to be fetched for it: the item `median-prices-msoa` of the list `m2-living`, of the source `ons-median-house-prices-msoa`, for the use `scoring`. Its one receipt, `f-545982134c5e`, says `validation_only`, which is what the gate was asked on the day it was fetched, and the first receipt of a file stands. So the receipt is put aside first, by the steps of section 7, "Put a receipt right", which allow that today for an edition or a period and not for a use: whether they may is yours to say. Then `uv run python -m burro_pipeline fetch --list m2-living --only median-prices-msoa` writes the receipt for `scoring`, and a build that takes `--list m2-living` holds the cost. Until then a build leaves the cost out by `input_has_one_receipt`, and the made-up release is the one that holds a cost.
- The list m2-places names the 33 files of the food hygiene register, which state their own edition. The build takes the newest of each that has a receipt, and its lock names the edition of each: section 7, "Which edition a build takes". So the first line reads `own_edition=33`. Two measures read the register: places to eat and drink, and pubs and bars. Each is worked out and left out of the release, and [the page on the food register](research/data/food-register.md) says what holds each back.
- `--built-at` is a time that has passed. It is an input and is never read from the clock, so that a build repeats. Give the hour of the last commit, and never a time later than the day the step is run: the service serves it as the time the release was built.
- Step 4 prints four lines of `step=derive status=ok` and six of `step=derive status=skipped`: green cover, transport noise, the nearest park, pubs and bars, places to eat and drink, and water close by. Each is worked out. Four are left out because what each measures is not what core's catalogue says the measure is: `measure_is_as_core_says=1`. Pubs and bars, and places to eat and drink, are left out because a check of their figures holds them back, whatever core says: `measure_is_not_held_back=1`. `coverage.md` beside the release has a section, "Worked out and left out", that says of each what it waits on.
- Step 5 says `4 measures`. With `--receipts` it holds every receipt in the evidence to the one that was committed.
- **Run step 5 before step 6, on the folder as it stands.** The service holds a release to `hashes.json`, which stands beside it and is signed by nobody. Until a release is approved and its hashes are committed, only `burro-release check` is proof that a release is what was built: [ADR 0018](adr/0018-a-real-release-is-served-with-its-evidence.md).
- One vibe has a band, Homes: section 17. A sentence with the word "leafy" in it ranks nothing, as in the first preview.
- The map shows what the first preview showed: nitrogen dioxide, homes per hectare, flats and homes built before 1919. Quiet, green and water are worked out and are not on it. Each waits on a decision, which the page lists.
- Green cover counts public parks and gardens alone. It is named for what it counts, which is not core's name for the measure, so a build leaves it out.

## 17. A preview, once the vibes were joined

The vibes and the builds of London were written apart, and were joined on 2026-09-24. A preview is now written at version 2 of the schema and version 4 of the catalogue. The service and `burro-release check` refuse one that was written before, as `shape_is_valid`, because its manifest does not say which way gritty is built: build again, under a new id, as section 16 says. Built again from the same files, every figure, outline and label is the same byte for byte as in the second preview.

What a build gives now that it did not give before:

| What | It is |
|---|---|
| The vibes a release carries | Twelve: Gritty, the scale that counts recorded crime, is one of them, and Works and warehouses is a vibe of its own beside it (ADR 0013, as amended on 2026-09-24). No area has a band on Gritty until 60 in 100 of its recipe is measured: a build holds main roads and transport noise, which are 25 |
| The vibe an area is placed on | One: Homes, which runs from Houses to Flats. Flats and homes per hectare are two of its three parts, 75 in 100 of its recipe. Every one of the 1,002 areas has a band, and its sentence ends "Worked out from 2 of its 3 parts, 75 of 100 by weight." |
| The vibes no area is placed on | The other ten. Homes built before 1919 are 35 in 100 of Age of buildings and 20 in 100 of Village feel, and no part of any other is measured. Each says that the area cannot be placed, and how many of its parts have a figure |
| What ranks the areas by a vibe | Houses or flats under Settings, or a sentence that holds "urban", "city living", "suburban" or "house with a garden". Each is read as assumed. Any other vibe leaves every area unranked, and each area says what it has no figure for |
| The map | A word of the shelf colours no area. Houses or flats is under "More words", and colours every area |
| More like this | Five areas for each of the 979 areas that have a figure for homes built before 1919. It is the one measure of the build that likeness may count on, so each sentence says "1 of the 1 measures" or "0 of the 1 measures", which is little |
| How nitrogen dioxide is said to be made | Modelled. Core says so since version 4 of the catalogue, and a build says how each figure was made from the method its evidence names |
| What `check` counts | 20,904 facts and 71,142 rows of evidence, where it counted 4,987 and 51,102: a fact for every vibe of every area, placed or not, and the facts of likeness |

Nobody has looked at a band of Homes against a street. It is worked out by a recipe whose weights are a judgement, from two figures that no person has checked. Two things are the founder's to say before it is shown to anyone else, and the contract lists each in section 13: whether a vibe may be shown on a release on which no audit has been run, and whether likeness may be said on one measure. Which way gritty is built for London is a third, and [the account of the first slice](design/slice-1.md) sets out both ways in section 10.

## 18. A preview with nine measures and three vibes

Five measures that were worked out and left out are now carried: transport noise, public parks and gardens, the nearest park, the nearest large park and main roads. Core names each for what its file holds, at version 5 of the catalogue. [The page on the first vibes on London](research/data/first-vibes-on-london.md) says what the release holds, which calls were made to bring each in, how each is undone, and what to look at first.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-24-21 --built-at 2026-09-24T07:00:00Z --out data/releases --list m1 --list m2-places"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-24-21 --receipts data/receipts` |
| 6 | The same, with `lon-2026-09-24-21` where section 15 has `lon-2026-09-24-01` |

What to know before you look:

- Step 4 prints nine lines of `step=derive status=ok` and one of `step=derive status=skipped`, for water close by. It takes about a minute: the roads are one file for Great Britain.
- Step 5 says `9 measures`.
- Three vibes have a band in every area: Houses or flats, Parks close by and Quiet streets. Each rests on two of its three parts, and its sentence says so. The other eight have none, and a search for one of them alone leaves every area unranked.
- Transport noise is named "Share of residents exposed to 55 dB or more of transport noise". The name says whose share it is, as the sentence of the measure does, and nothing of who they are. It is the one name that may say residents: decided on 2026-09-24.
- Main roads are shown, and no area is ranked on them alone: no audit of the figure has been run. Quiet streets rests on them all the same.
- The distance to a park is a straight line to a way in that its publisher marks, and its name says so.
- Fine particles, water close by and what a home sells for are still left out. The page says what each waits on.
- Everything sections 16 and 17 say before you look still stands, but for what they say is left out and which vibe has a band.

## 19. A preview with eleven measures, once the catalogue took what was decided

Five decisions of 2026-09-24 are in the catalogue at version 11, and the engine is 1.11.0. Gritty is one vibe, which counts recorded crime. Places to eat and drink are shown as a count and ranked on for each 1,000 homes. Going out is made of places to eat and drink, a high street and culture venues, and counts no pub. What homes sell for is a measure, the second reading of a word for a smart area. What is said of the place weighs more than a journey and more than a budget. [ADR 0013](adr/0013-vibes-are-the-centre.md) and [ADR 0021](adr/0021-a-price-is-shown-as-the-publisher-gives-it.md) say each.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-24-93 --built-at 2026-09-24T18:00:00Z --out data/releases --list m1 --list m2-living --list m2-places --list m2-culture --list m10-land-use"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-24-93 --receipts data/receipts` |
| 6 | The same, with `lon-2026-09-24-93` where section 15 has `lon-2026-09-24-01` |

What to know before you look:

- The first line reads `inputs=59 missing=16`. Sixteen files of the five lists have no receipt, and are no part of the build. The police file, the land use file, the town centres and the workbook of median prices are among them.
- Step 4 prints eleven lines of `step=derive status=ok` and three of `step=derive status=skipped`: what homes sell for, by `input_has_one_receipt`, pubs and bars, by `measure_is_not_held_back`, and water close by, by `measure_is_as_core_says`. It prints `step=cost status=skipped` too.
- Step 5 says `11 measures`, and the check counts 29,015 facts and 74,148 rows of evidence. Built twice from the same files and the same commit, the two folders hold the same bytes.
- Places to eat and drink have a figure in 992 of the 1,002 areas, both as a count and for each 1,000 homes. Ten areas at the edge of London have homes outside it within reach, and no figure. The count is shown and no area is ranked on it: a wish for places to eat and drink is ranked on the second figure.
- Three vibes have a band in every area, as in section 18: Houses or flats on 75 in 100 of its recipe, and Parks close by and Quiet streets on 70 each.

What each of the other nine vibes holds, and what it waits on:

| Vibe | It holds, in 100 | It waits on |
|---|---|---|
| Going out | 45: places to eat and drink for each 1,000 homes | A high street within reach, 30, and culture venues, 25. Either gives it a band. Pubs and bars join when a second source confirms them |
| Food and drink | 40: the count of places to eat and drink | Independent places, 40, and kinds of food, 20 |
| Age of buildings | 35: homes built before 1919 | Conservation areas, 25, listed buildings, 20, and homes built since 2000, 20 |
| Leafy | 30: public parks and gardens | Residential gardens, 40, and woodland, 30, which are land use |
| Gritty | 25: main roads, 15, and transport noise, 10 | Recorded criminal damage, 30, recorded anti-social behaviour, 15, and works and warehouses, 30, which are land use |
| Family amenities | 25: the nearest park | Primary schools, 40, and play space, 35 |
| Village feel | 20: homes built before 1919 | Independent places, 25, a small centre, 20, a compact centre, 20, and conservation areas, 15 |
| Everyday on foot | 0 | The walk to groceries, a high street, a station, a GP surgery and a pharmacy |
| Works and warehouses | 0 | Land use |

- What homes sell for is left out, as the cost is, and for the same reason: the one receipt of the workbook says `validation_only`. Section 16 says how the file is fetched for `scoring`. Until it is, a word for a smart area is answered on London with both its readings listed as not in this data: Gritty has no band, and the release holds no price.
- A sentence that asks for quiet and for parks is ranked on those two. What it says of a journey, a budget, culture and the character of a place is listed as what this data cannot answer, and nothing stands in for any of it.
- Everything sections 16 to 18 say before you look still stands, but for what they say is left out and which measures are carried.

## 20. A preview with 28 measures, once core named the measures as they are built

The catalogue is at version 12, and the engine is 1.12.0. Core names each measure that was built as it is built, so a build carries it: six distances as straight lines, recorded incidents for each 1,000 homes a year, two kinds of land and homes near water by what is counted, and cultural venues as a count that is shown and a rate that is ranked on. Works and warehouses is a part of Gritty, and no vibe of its own. [What core needs](design/what-core-needs.md) says each, and what is still left out.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-24-94 --built-at 2026-09-24T19:00:00Z --out data/releases --list m1 --list m2-places --list m2-living --list m2-culture --list m10-health --list m10-land-use --list m11-age-and-households --list m11-high-streets --list m11-outdoor-space"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-24-94 --receipts data/receipts` |
| 6 | The same, with `lon-2026-09-24-94` where section 15 has `lon-2026-09-24-01` |

It names every list that holds a receipt. The list of journeys holds none, and is left out.

What to know before you look:

- The first line reads `inputs=73 missing=10`. Ten files of the nine lists have no receipt, and are no part of the build: the workbooks of prices and of sales, the files of prices paid, the list of pharmacies, the high street boundaries, the streets, and the lookup between the areas of two censuses.
- Step 4 prints 28 lines of `step=derive status=ok` and five of `step=derive status=skipped`. The size and the shape of a town centre and what there is to do in parks are left out by `measure_is_as_core_says`, and each waits on the founder. Pubs and bars are left out by `measure_is_not_held_back`. What homes sell for is left out by `input_has_one_receipt`, and `step=cost` is skipped for the same reason.
- Step 5 says `28 measures`, and the check counts 44,966 facts.
- Every area has a figure for 20 of the 28. The nearest station has one in 970 of the 1,002 areas, the nearest town centre in 976, homes built before 1919 in 979, homes built since 2000 in 999, and places to eat and drink and cultural venues in 992 each, as a count and as a rate. An area at the edge of London has homes within reach outside it, and no figure.

Eight of the eleven vibes have a band:

| Vibe | It holds, in 100 | Areas with a band | What is not held |
|---|---|---|---|
| Leafy | 100 | 1,002 | |
| Going out | 100 | 992 | |
| Age of buildings | 100 | 1,001 | |
| Family amenities | 100 | 1,002 | |
| Gritty | 100 | 1,002 | |
| Houses or flats | 75 | 1,002 | Private outdoor space, 25 |
| Quiet streets | 70 | 1,002 | Clusters of late venues, 30 |
| Parks close by | 70 | 1,002 | What there is to do in parks, 30 |
| Everyday on foot | 45 | 0 | The walk to a food shop, 25, a GP, 15, and a pharmacy, 15 |
| Food and drink | 40 | 0 | Independent places, 40, and kinds of food, 20 |
| Village feel | 35 | 0 | Independent places, 25, a small centre, 20, and a compact centre, 20 |

- Family amenities puts inner London first. It counts primary schools within 800 metres and the distance to a play space and to a park, and each is nearer where homes stand closer together. Look at its map before it is served.
- A search that asks for a measure by name puts an area with no figure for it below every area that has one. So the 32 areas with no figure for a station stand last for a person who asks to be near one, and stand where their fit puts them for a person who does not.
- A budget and a journey are still listed as what this data cannot answer, and a word for a smart area is answered by Gritty alone: the release holds no price.
- Everything sections 16 to 19 say before you look still stands, but for what they say is left out and which vibe has a band.

## 21. A preview whose areas bear names

Until now every area of a preview read as the statistics office labels it: a borough and a number. Given the draft of London's named areas, each area bears the name of the drafted neighbourhood that holds most of its output areas, with the label beside it, and says that the name is a draft. [ADR 0025](adr/0025-an-area-bears-a-drafted-name-and-says-so.md) holds the decision, and section 20 of [the areas design](design/london-data-areas.md) what was counted.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| Before 4 | `uv run python -m burro_pipeline.areas.draft_run --out FOLDER`, in the terminal where step 3 named the store. It makes the draft of names from the store, in about four minutes. `FOLDER` is outside what git tracks |
| 4 | `make preview ARGS="--release-id lon-2026-09-24-96 --built-at 2026-09-24T21:00:00Z --out data/releases --names FOLDER --list m1 --list m2-places --list m2-living --list m2-culture --list m10-health --list m10-land-use --list m11-age-and-households --list m11-high-streets --list m11-outdoor-space"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-24-96 --receipts data/receipts` |
| 6 | The same, with `lon-2026-09-24-96` where section 15 has `lon-2026-09-24-01` |

Once names have been decided at the review desk, give `--names` the folder `gazetteer` that `python -m desk compile` wrote. A name a person chose is then served as they spelt it, and says that it was checked.

What to know before you look:

- A third line is printed after `step=cells`: `step=names status=ok release=lon-2026-09-24-96 areas=1002 named=1002 files=2`. It names no area. The first line reads `inputs=76`: the three files read of the draft are named in the lock beside the 73 files of publishers.
- `names.csv` beside the release lists every area with its borough, its label, the name it bears, who wrote it and whether a person has checked it. It names places, so it is written where the build writes and is never committed. `build.json` holds the counts.
- All 1,002 areas bear a name, under 458 names. 312 names are borne by two areas or more, and 806 areas say the side they lie on, as "north". 16 areas say what another area of their borough says: the label beside each tells them apart.
- Every name is a draft. No person has read one. An area at the edge of a neighbourhood bears the name of the neighbourhood that holds most of it, and 120 areas have under half of their output areas in the neighbourhood whose name they bear. 28 areas bear a name that the draft marks as perhaps a street or a building: the mark falls on names that are wrong and on names everybody uses.
- No figure moves. The files of a release that hold its figures are the same bytes with a draft of names and with none, so a search ranks the same areas in the same order.
- A search by name finds the areas that bear it: the box beside the prompt lists them, each as a link to its page. In a sentence, a name that one area alone bears is read as the name of an area always was: "not in" before it leaves the area out. A name that several areas bear names none of them, so the reader makes nothing of it. Of the 819 sentences of the reader's cases, none is read otherwise for the names.
- The build stops, and writes nothing, where the draft was made from a file of names that is no file of the build. Make the draft again from the store the build reads, and name the lists `m1` and `m2-places`, which hold the two files that write a name.
- Everything section 20 says before you look still stands.

## 22. A preview with 35 measures, once cafes, gyms and pubs were counted

The catalogue is at version 13, and the engine is 1.12.0. Cafes, gyms and pubs are counted from the file of places, each as a count that is shown and a figure for each 1,000 homes that is ranked on. Homes near a cluster of pubs and bars are measured, so Quiet streets rests on its whole recipe. Pubs and bars are in Going out again. [What the file gave](research/data/cafes-gyms-and-pubs.md) says each, and why pubs are counted from the file of places and no longer from the food register.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-24-95 --built-at 2026-09-24T22:00:00Z --out data/releases --list m1 --list m2-places --list m2-living --list m2-culture --list m10-health --list m10-land-use --list m11-age-and-households --list m11-high-streets --list m11-outdoor-space"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-24-95 --receipts data/receipts` |
| 6 | The same, with `lon-2026-09-24-95` where section 15 has `lon-2026-09-24-01` |

What to know before you look:

- The first line reads `inputs=73 missing=10`, as in section 20. No file was fetched for this build: the cafes, the gyms and the pubs are in the part of the file of places that the cultural venues are counted from.
- Step 4 prints 35 lines of `step=derive status=ok` and four of `step=derive status=skipped`. The size and the shape of a town centre and what there is to do in parks are left out by `measure_is_as_core_says`. What homes sell for is left out by `input_has_one_receipt`. No measure is held back.
- Step 5 says `35 measures`, and the check counts 51,920 facts.
- Every area has a figure for 21 of the 35. The six figures of cafes, gyms and pubs have one in 992 of the 1,002 areas, as places to eat and cultural venues do: an area at the edge of London has homes within reach outside it, and no figure. Homes near a cluster of pubs and bars have a figure in every area.

The same eight of the eleven vibes have a band. No vibe gained one:

| Vibe | It holds, in 100 | Areas with a band | What moved |
|---|---|---|---|
| Going out | 100 | 992 | Pubs and bars are 35 in 100 of it. 699 areas keep their band, 292 move by one and 1 by two. The order of the areas is the same at 0.97 |
| Quiet streets | 100, where it held 70 | 1,002 | Homes near a cluster of pubs and bars are 30 in 100 of it. 704 areas keep their band, 296 move by one and 2 by two. The order of the areas is the same at 0.96 |
| The other nine | As in section 20 | As in section 20 | Nothing |

- A wish for cafes, for a gym or for pubs is applied, and ranks on the figure for each 1,000 homes. The ten areas with no figure are listed apart, with what they lack.
- A rate takes few values: many areas tie on it, so a search that asks for cafes alone orders groups of areas, and the rest of the search orders the areas within a group.
- Every figure of pubs says that the file holds fewer pubs toward the edge of London. Look at the map of Going out at the edge before it is served.
- Everything sections 16 to 20 say before you look still stands, but for what they say is left out and what Going out and Quiet streets hold.

## 23. A preview with 30 measures, once a food shop and a GP practice were measured

It was built before the streams of 2026-09-24 were joined, from the measures of section 20. The catalogue is at version 13, and the engine is 1.12.0. Two measures joined the table of a build. The nearest food shop is read from the file of places that the list `m2-culture` takes, and the nearest GP practice from the report of practices of the list `m10-health`, each as a straight line in metres. So Everyday on foot holds 85 in 100 of its recipe, and has a band. [What core needs](design/what-core-needs.md) says each, and what is still left out.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-24-96 --built-at 2026-09-24T22:00:00Z --out data/releases --list m1 --list m2-places --list m2-living --list m2-culture --list m10-health --list m10-land-use --list m11-age-and-households --list m11-high-streets --list m11-outdoor-space"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-24-96 --receipts data/receipts` |
| 6 | The same, with `lon-2026-09-24-96` where section 15 has `lon-2026-09-24-01` |

It names every list that holds a receipt, as section 20 does. Step 4 takes about eight minutes.

What to know before you look:

- The first line reads `inputs=73 missing=10`, as in section 20. The list of pharmacies is one of the ten: its period is stated in the list since, and it has no receipt until it is fetched again.
- Step 4 prints 30 lines of `step=derive status=ok` and five of `step=derive status=skipped`, which are the five of section 20.
- Step 5 says `30 measures`, and the check counts 46,962 facts.
- The nearest food shop has a figure in every area. The nearest GP practice has one in 994 of the 1,002: a practice outside London is placed nowhere, so a home near the edge of London has no distance.
- A sentence that says "walkable", "near a supermarket", "near a GP" or "shops nearby" is read and ranked on. "Near a pharmacy" is read, and listed as what this data cannot answer.

Nine of the eleven vibes have a band. Eight are as section 20 has them, and the ninth is Everyday on foot:

| Vibe | It holds, in 100 | Areas with a band | What is not held |
|---|---|---|---|
| Everyday on foot | 85 | 984 | The nearest pharmacy, 15 |

- 957 areas rest on all four parts that are held. 27 rest on three of them, at 60 to 70 in 100, and 18 have no band: each is at the edge of London, where the nearest station, town centre or GP practice may stand outside it.
- Everyday on foot is mostly a map of how built up a place is. It stands in the order of homes per hectare at 0.76 by rank, and of the distance from the middle of London's homes at -0.65. Of the 196 areas of its highest band, 14 are no denser than the middle area of London, and of the 197 of its lowest, 5 are denser. It finds much the same areas as Going out, at 0.81. Look at its map before it is served.
- A food shop is a grocer, a supermarket or a convenience store, as the file of places gives it. Nothing says how large a shop is or what it sells, so a corner shop counts as a supermarket does.

## 24. A preview with 31 measures, once a pharmacy was measured

It was built before the streams of 2026-09-24 were joined, as section 23 was. The catalogue is at version 13, and the engine is 1.12.0. One measure joined the table of a build: the nearest pharmacy, read from the pharmacy list of the list `m10-health`, as a straight line in metres. So Everyday on foot rests on the whole of its recipe. No recipe moved for it: Everyday on foot says, first of what it cannot see, that it is mostly a map of how built up a place is. [What core needs](design/what-core-needs.md) says each, and what is still left out.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-25-51 --built-at 2026-09-24T22:30:00Z --out data/releases --list m1 --list m2-places --list m2-living --list m2-culture --list m10-health --list m10-land-use --list m11-age-and-households --list m11-high-streets --list m11-outdoor-space"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-25-51 --receipts data/receipts` |
| 6 | The same, with `lon-2026-09-25-51` where section 15 has `lon-2026-09-24-01` |

It names every list that holds a receipt, as section 23 does. Step 4 takes about nine minutes.

What to know before you look:

- The first line reads `inputs=74 missing=9`. The list of pharmacies has its receipt, so nine files of the nine lists have none.
- Step 4 prints 31 lines of `step=derive status=ok` and five of `step=derive status=skipped`, which are the five of section 20.
- Step 5 says `31 measures`, and the check counts 47,964 facts.
- The nearest pharmacy has a figure in every area. Its figure is of the list of a quarter, from April to June 2026, and says no day.
- A sentence that says "near a pharmacy" or "a chemist nearby" is read and ranked on. A word for a doctor or for a chemist is heard only where the words beside it say near, so "I am a doctor" asks for nothing.

Nine of the eleven vibes have a band, as in section 23. Everyday on foot is the one that moved:

| Vibe | It holds, in 100 | Areas with a band | What is not held |
|---|---|---|---|
| Everyday on foot | 100 | 988 | Nothing |

- 957 areas rest on all five parts. 31 rest on fewer, at 60 to 85 in 100, and 14 have no band: each is at the edge of London, where the nearest station, town centre or GP practice may stand outside it. Four areas gained a band with the pharmacy, and none lost one.
- The pharmacy moved the bands little. Of the 984 areas that had a band before, 846 are in the band they were in, 72 are one band higher and 66 one band lower. None moved by two. The two orders agree at 0.99 by rank.
- Everyday on foot is still mostly a map of how built up a place is, and says so beside its band. It stands in the order of homes per hectare at 0.77 by rank, and of the distance from the middle of London's homes at -0.66. Of the 197 areas of its highest band, 13 are no denser than the middle area of London, and of the 198 of its lowest, 5 are denser. It finds much the same areas as Houses or flats towards Flats, at 0.80, and as Going out, at 0.79.
- A pharmacy that serves by post alone is counted as any other: the list has no column that says which they are.

## 25. A preview with the brands, and with what homes sell for

It was built before the streams of 2026-09-24 were joined, from the measures of section 20. The catalogue is at version 13. It holds the chains of grocers, gyms and coffee as measures ([decision record 0026](adr/0026-the-chains-in-a-place-are-measured-by-a-table-of-tiers.md)), and the list `m2-culture` takes the file of places a second time, with the brand of each place. The workbook of median prices has a receipt for scoring, so the build holds what homes sell for.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-24-96 --built-at 2026-09-24T22:30:00Z --out data/releases --list m1 --list m2-places --list m2-living --list m2-culture --list m10-health --list m10-land-use --list m11-age-and-households --list m11-high-streets --list m11-outdoor-space"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-24-96 --receipts data/receipts` |
| 6 | The same, with `lon-2026-09-24-96` where section 15 has `lon-2026-09-24-01` |

What to know before you look:

- The first line reads `inputs=75 missing=9`. The build takes about eleven minutes, of which the brands take under one.
- Step 4 prints 76 lines of `step=derive status=ok` and six of `step=derive status=skipped`. The nearest Third Space and the nearest Gymbox are left out by `measure_has_a_figure`: the file of places holds no place of either. The size and the shape of a town centre and what there is to do in parks are left out by `measure_is_as_core_says`, and pubs and bars by `measure_is_not_held_back`, as before.
- `step=cost` reads `status=ok` with 2,544 rows: what a home of each kind sells for, where the publisher gives it.
- Step 5 says `76 measures`, and the check counts 78,733 facts.
- The mix of brands has a figure in 990 areas and independent places in 992. The nearest place of a chain has one only where a place stands within 2,000 m of half an area's homes: 989 areas for the commonest chain and 21 for the rarest that the file holds.

Ten of the eleven vibes have a band. Food and drink and Village feel are the two that had none:

| Vibe | It holds, in 100 | Areas with a band | What is not held |
|---|---|---|---|
| Food and drink | 80 | 992 | Kinds of food, 20 |
| Village feel | 60 | 969 | A small centre, 20, and a compact centre, 20 |
| Everyday on foot | 45 | 0 | The walk to a food shop, 25, a GP, 15, and a pharmacy, 15 |

The other eight are as section 20 has them.

- **Village feel does not find villages, and the build that was made placed areas on it.** Since then core places it only where the size or the shape of a town centre has a figure, so a build made now places no area on it: [the contract](design/contract.md), section 3.2. It holds the least a band is given on, and nothing of a town centre. [The page on brands](research/data/brands.md), section 7, says what it finds. Look at its map before it is served.
- A word for a smart area is answered three ways: the mix of brands, Gritty, and what homes sell for.
- A budget is answered. A firm limit of 400,000 pounds for a flat leaves out 397 areas, and 75 more have no price for a flat and say so.
- A journey is still listed as what this data cannot answer.

## 26. A preview with 32 measures, once core held who lived somewhere

The catalogue is at version 13, and the engine is 1.12.0. Core holds four measures of who lived in an area at the census of 2021, by their age or by what their households are made of, and two vibes that hold one each: Family area and Young professionals. [The design of those measures](design/residents-age-and-households.md) says what was decided, holds the row of the proxy audit, and says what this build shows of the two vibes.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-24-80 --built-at 2026-09-24T23:45:00Z --out data/releases --list m1 --list m10-health --list m10-land-use --list m11-age-and-households --list m11-high-streets --list m11-outdoor-space --list m2-culture --list m2-living --list m2-places"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-24-80 --receipts data/receipts` |
| 6 | The same, with `lon-2026-09-24-80` where section 15 has `lon-2026-09-24-01` |

It names every list that holds a receipt, as section 20 does. The list of journeys holds none, and is left out.

What to know before you look:

- The first line reads `inputs=73 missing=10`, as in section 20.
- Step 4 prints 32 lines of `step=derive status=ok` and five of `step=derive status=skipped`. The four that are new are of the source `ons-census-2021-age-and-household-tables`, and each has a figure in each of the 1,002 areas. What is left out is what section 20 leaves out, by the same rules.
- Step 5 says `32 measures`, and the check counts 50,978 facts.
- Each of the four is a share in 100, given to one decimal place, from the statistics office's own row for the area. The release and its evidence hold no count of people.

Ten of the thirteen vibes have a band: the eight of section 20, as they were there, and the two that are new.

| Vibe | It holds, in 100 | Areas with a band | What is not held |
|---|---|---|---|
| Family area | 100 | 1,002 | |
| Young professionals | 100 | 994 | |

- Neither is on a result unless it was asked for, and neither is in the list of what an area has most or least of. A map may be coloured by each, and a comparison holds each.
- A phrase for either is offered and never applied: "young professionals, lively, near a station" applies nothing, and offers Young professionals, Going out and the nearest station. A wish for fewer of anyone is answered with the notice, and nothing is offered for it.
- Young professionals stands at 0.84 with Houses or flats across London's areas, and Family area at 0.08. Look at the map of each before it is served: the design says what a Londoner would and would not know in each.
- Everything sections 16 to 20 say before you look still stands, but for which measures are carried and which vibe has a band.

## 27. A preview with prices from the sales, two more figures of homes, and household income beside it

The catalogue is at version 13, and the engine is 1.13.0. What a home sells for is worked out from the sales of three years, for each kind of home, and a firm budget has a margin. The council tax bands and the rise in prices are measures. Household income is written to a folder of its own beside the release, to be shown and never ranked on. [The page of research](research/data/prices.md) holds the counts, and decision records [0021](adr/0021-a-price-is-shown-as-the-publisher-gives-it.md) and [0028](adr/0028-household-income-is-shown-and-never-ranked-on.md) what was decided.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-25-70 --built-at 2026-09-25T00:00:00Z --out data/releases --list m1 --list m2-places --list m2-living --list m2-culture --list m10-health --list m10-land-use --list m11-age-and-households --list m11-high-streets --list m11-outdoor-space --list m12-household-income --list m12-public-transport"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-25-70 --receipts data/receipts --income data/releases/lon-2026-09-25-70-income` |
| 6 | The same, with `lon-2026-09-25-70` where section 15 has `lon-2026-09-24-01`. The service finds the folder of income beside the release |

It names every list that holds a receipt. The list of journeys holds none, and is left out. Step 4 takes about seven minutes: three files of sales hold 2.7 million rows.

What to know before you look:

- The first line reads `inputs=81 missing=6`. Six files of the eleven lists have no receipt, and are no part of the build: the workbooks of lower-quartile prices and of counts of sales, the list of pharmacies, the high street boundaries, the streets, and the lookup between the areas of two censuses.
- Step 4 prints 32 lines of `step=derive status=ok` and four of `step=derive status=skipped`, which are the four that section 20 names. The council tax bands have a figure in 982 of the 1,002 areas, and each rise in all of them.
- `step=cost` reads `status=ok source=hmlr-price-paid areas=1002 rows=2859 files=5`. A flat has a price in 984 areas, a terraced house in 940, a semi-detached house in 653 and a detached house in 282. Each row says how many sales it rests on, and none rests on fewer than 10.
- `step=income` reads `status=ok source=ons-income-estimates-small-areas areas=1002 values=1002 files=1`. It is written after the release is checked, to the folder `lon-2026-09-25-70-income`. The release holds nothing of it: no measure, no fact and no row of evidence.
- Step 5 says `32 measures`, and then `1002 areas, 1002 with an estimate, real` for the income. The check counts 51,813 facts.
- **A budget is now answered.** A firm £400,000 for a flat leaves out 231 areas, where it left out 424 with no margin. Most of them are in nine boroughs of inner and west London. An area that is kept with its middle price over the budget says how far over, and that about half of the flats sold there went for less.
- A price is of homes of every size. "A 1 bed flat" is read as a flat, and the offer says that Burro holds no price by the number of bedrooms.
- A word for a smart area is offered three things: Gritty towards Polished, what homes sell for, and the council tax bands. A word for a place on the rise is offered the rise over five years and over ten. None is applied until it is pressed.
- **A journey is still what this data cannot answer.** The release holds no place to reach, so "35 to 40 minutes from" a place is listed as not in this data, and the first areas of a search may lie far from it.
- The page of an area offers household income under its own heading, after every figure of the place. It is asked for when it is opened. No census figures are offered: no build writes a real census yet.
- Everything sections 16 to 20 say before you look still stands, but for what they say of a price and of a budget.

## 28. A preview with private outdoor space worked out, and held back

**Since 2026-09-25 a build carries the measure.** The proxy audit it was held back for is dropped, and section 31 says what a build holds with it. What follows is how things stood when this preview was made.

The catalogue is at version 13, and the engine is 1.12.0. Core names private outdoor space as it is built: addresses with private outdoor space, by MSOA. The measure is on the table of measures and is held back from every release, until its row of the proxy audit has passed. So this preview carries what the preview of section 20 carried, and works one more measure out.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-25-51 --built-at 2026-09-25T00:00:00Z --out data/releases --list m1 --list m2-places --list m2-living --list m2-culture --list m10-health --list m10-land-use --list m11-age-and-households --list m11-high-streets --list m11-outdoor-space"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-25-51 --receipts data/receipts` |
| 6 | The same, with `lon-2026-09-25-51` where section 15 has `lon-2026-09-24-01` |

It names the nine lists that section 20 names. Step 4 takes about ten minutes.

What to know before you look:

- The first line reads `inputs=77 missing=6`. Six files of the nine lists have no receipt, and are no part of the build: the workbooks of median prices, of sales and of the lower quartile, the list of pharmacies, the high street boundaries and the streets. The lookup between the areas of two censuses and the three yearly files of prices paid have theirs since 2026-09-24.
- Step 4 prints 28 lines of `step=derive status=ok` and six of `step=derive status=skipped`. Five are those of section 20. The sixth is private outdoor space, by `measure_is_not_held_back`: it is worked out, and it is left out whatever core says of it.
- Step 5 says `28 measures`, and the check counts 44,966 facts, as in section 20. The table of vibes of section 20 stands: each vibe holds as much of its recipe as it did, and has a band in as many areas. Houses or flats rests on 75 in 100 of its recipe in all 1,002 areas.

What was worked out of private outdoor space, and is in no release:

| | |
|---|---|
| Areas with a figure | 963 of 1,002. Each is an area that the statistics office's lookup marks as unchanged since 2011, and the workbook holds a row for every one |
| Areas with none | 39. 38 are parts of the 18 areas of 2011 that were split, 16 into two and two into three. One was made by joining two areas of 2011. They lie in 14 boroughs |
| Were a split carried | 1,001 areas would have a figure. No build carries one: `CARRIED` in `derive/areas_of_2011.py` holds the mark of no change alone, and to add the mark of a split is the founder's to decide |
| The figure | Addresses with private outdoor space, in 100 of the addresses of the area, as at April 2020. The lowest is 7.2, a quarter of the areas are under 77.0, the middle is 86.1, a quarter are over 91.5, and the highest is 99.6 |
| What it follows | Flats as a share of homes, at -0.77 as a rank correlation: where more homes are flats, fewer addresses have outdoor space. Homes per hectare at -0.46, homes built since 2000 at -0.58, transport noise at -0.56, and gardens as a share of land at 0.47 |

What Houses or flats would be if the measure joined its recipe, at 25 in 100 and read from its low end. It was worked out beside the build, by the functions a build works a vibe out with, and nothing of it is served. `packages/pipeline/tests/derive/test_private_outdoor_space_on_the_real_files.py` holds each count.

| | |
|---|---|
| What the vibe would rest on | Its whole recipe in 963 areas, and 75 in 100 in the 39 with no figure. Every area would still have a band |
| Areas that would keep their band | 800 of 1,002 |
| Areas that would move | 101 by one band towards Flats, and 101 by one band towards Houses. None by two |
| The order of the areas | 0.98 the same, as a rank correlation. Where an area stands among the areas, in 100, would move by 3.9 in the middle area, by under 10.3 in nine areas in ten, and by 16.9 at most |
| The ends | Of the 201 areas in the band nearest Houses, 179 would stay in it. Of the 200 in the band nearest Flats, 177 would |
| The 39 areas with no figure | 38 would keep their band, and one would move one band towards Flats as the areas round it moved. 22 of them would stand in the band nearest Flats and 10 in the next |

- The measure says much of what flats as a share of homes already says, so the vibe moves little. What it adds is the fifth of the areas that would change band.
- An area with no figure is not an area with no outdoor space. Most of the 39 stand towards the end of flats, so a recipe that holds the measure rests on less in the areas where it says most.
- Before the measure joins, its row of the proxy audit is written and passes: the design of the vibes asks that it is under 0.3 on every table of the audit. No audit can be run yet. The tables it is run on are gated in the licence registry until a store the product cannot read exists, with its check in CI, and until the rule of the audit is written. Each is the founder's.
- Everything sections 16 to 20 say before you look still stands.

## 29. A preview from every list that holds a receipt, once the work of 2026-09-24 and 2026-09-25 was joined

The catalogue is at version 13, and the engine is 1.13.0. This is the one build that holds what sections 21 to 28 each built apart: the names, the cafes, the gyms and the pubs, the food shop, the GP practice and the pharmacy, the brands, how near stops are and the stations as places to reach, who lived somewhere, what each kind of home sold for with the bands and the rises, and household income beside it.

Do everything as section 15 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| Before 4 | `uv run python -m burro_pipeline.areas.draft_run --out FOLDER`, as section 21 says |
| 4 | `make preview ARGS="--release-id lon-2026-09-25-01 --built-at 2026-09-25T02:00:00Z --out data/releases --names FOLDER --list m1 --list m2-places --list m2-living --list m2-culture --list m2-stations --list m5-journeys --list m10-health --list m10-land-use --list m11-age-and-households --list m11-outdoor-space --list m12-household-income --list m12-public-transport"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-25-01 --receipts data/receipts --income data/releases/lon-2026-09-25-01-income` |
| 6 | The same, with `lon-2026-09-25-01` where section 15 has `lon-2026-09-24-01`. The service finds the folder of income beside the release |

It names the twelve lists that hold a receipt. The draft of names takes about two minutes, and step 4 about eight.

What to know before you look:

- The first line reads `inputs=89 missing=3`. Three files of the lists have no receipt, and are no part of the build: the street extract, and the workbooks of sales and of the lower quartile. The three files read of the draft of names are among the 89.
- Step 4 prints 98 lines of `step=derive status=ok` and six of `step=derive status=skipped`. The nearest place of two chains, Gymbox and Third Space, has a figure for no area. The size and the shape of a town centre and what there is to do in parks keep core's names. Private outdoor space is held back.
- `step=names` reads `named=1002`. `step=cost` reads `rows=2859`: what each kind of home sold for, from the sales of three years. `step=places` reads `rows=641`: the stations, each a place to reach. `step=income` reads `values=1002`.
- Step 5 says `98 measures, 641 destinations, 641 places`, and then that the folder of income holds 1,002 areas with an estimate. The check counts 104,010 facts.
- Of the 98 measures, 73 can be ranked on. The 25 that are shown and never ranked on are the five counts of places and the stops of buses, the 18 measures of the tiers, and the main roads.
- It holds no journey time and no rent. A journey by public transport to a station is estimated for a search, from distance, and is said to be an estimate.

Thirteen of the fourteen vibes place an area:

| Vibe | Of its recipe, in 100 | Areas with a band | What it waits on |
|---|---|---|---|
| Leafy, Quiet streets, Family amenities, Well connected, Gritty, Family area | 100 | 1,002 | |
| Age of buildings | 100 | 1,001 | |
| Young professionals | 100 | 994 | |
| Going out | 100 | 992 | |
| Everyday on foot | 100 | 988 | |
| Food and drink | 80 | 992 | Kinds of food nearby |
| Houses or flats | 75 | 1,002 | Private outdoor space, which is held back |
| Parks close by | 70 | 1,002 | What there is to do in parks |
| Village feel | 60 | None | The size and the shape of a town centre |

Village feel holds 60 in 100 of its recipe in 969 areas, which would be enough for a band. It places none: core places it only where the size or the shape of a town centre has a figure ([the contract](design/contract.md), section 3.2).

## 30. A preview with the high streets in its lock, and Village feel held off as it was

The catalogue is at version 13, and the engine is 1.13.0, as in section 29. Nothing of core changed. The build names one list more, `m11-high-streets`, whose one file has its receipt since 2026-09-24. It was made to show what a second try at Village feel changed of a build, which is nothing that a person sees: [the page on high streets](research/data/high-streets.md) says what the try found.

Do everything as section 29 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| Before 4 | Nothing. This build was given no draft of names, so each area is under its publisher's label |
| 4 | `make preview ARGS="--release-id lon-2026-09-25-21 --built-at 2026-09-25T06:00:00Z --out data/releases --list m1 --list m2-places --list m2-living --list m2-culture --list m2-stations --list m5-journeys --list m10-health --list m10-land-use --list m11-age-and-households --list m11-high-streets --list m11-outdoor-space --list m12-household-income --list m12-public-transport"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-25-21 --receipts data/receipts --income data/releases/lon-2026-09-25-21-income` |
| 6 | The same, with `lon-2026-09-25-21` where section 15 has `lon-2026-09-24-01` |

It names the thirteen lists that hold a receipt. Step 4 takes about ten minutes, and step 5 about three.

What to know before you look:

- The first line reads `inputs=87 missing=3`. The file of high streets is one of the 87. The 89 of section 29 held the three files of a draft of names, which this build was not given.
- **The file of high streets is in the lock, and no measure of the build reads it.** `derive/highstreet_conserved.py` reads it, and is on no list of a build: core holds no feature for it. A test on the real files works it out, and 925 of the 1,002 areas have a figure.
- Step 4 prints 98 lines of `step=derive status=ok` and six of `step=derive status=skipped`, which are the six of section 29.
- Step 5 says `98 measures, 641 destinations, 641 places`. The check counts 104,010 facts, as in section 29.
- Thirteen of the fourteen vibes place an area, and each places as many as in section 29. Village feel places none.

What a person is told who asks for a village, with no model and the rules reading:

| Typed | What the service does |
|---|---|
| "a village feel" | Applies nothing, and says that Village feel is not in this data. It offers nothing in its place, and the ranking is the one a search with nothing said gives |
| "somewhere with a real identity" | Applies nothing, and says that Village feel is not in this data. It offers two of the three ways it holds for a word of character: Age of buildings towards Historic, and nearer a town centre. Its note names those two. When the build was made the note named a village feel as well, which no press could give: core was put right the same day |

No line the service wrote holds a word that was typed.

## 31. A preview that carries private outdoor space, once the proxy audit was dropped

The catalogue is at version 13, and the engine is 1.13.0. It is the build of section 29, made again from the same files and the same lists. Private outdoor space was held back from every release for want of a row of the proxy audit, and for no other reason. The founder dropped the audit on 2026-09-25 ([ADR 0006](adr/0006-rank-places-not-residents.md), as amended that day), so nothing holds the measure back, and this preview carries it.

Do everything as section 29 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| 4 | `make preview ARGS="--release-id lon-2026-09-25-31 --built-at 2026-09-25T05:00:00Z --out data/releases --names FOLDER --list m1 --list m2-places --list m2-living --list m2-culture --list m2-stations --list m5-journeys --list m10-health --list m10-land-use --list m11-age-and-households --list m11-outdoor-space --list m12-household-income --list m12-public-transport"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-25-31 --receipts data/receipts --income data/releases/lon-2026-09-25-31-income` |
| 6 | The same, with `lon-2026-09-25-31` where section 15 has `lon-2026-09-24-01` |

What to know before you look:

- Step 4 prints 99 lines of `step=derive status=ok` and five of `step=derive status=skipped`. The five are those of section 29 without private outdoor space: the nearest place of two chains has a figure for no area, and the size and the shape of a town centre and what there is to do in parks keep core's names.
- Step 5 says `99 measures, 641 destinations, 641 places`.
- Private outdoor space has a figure in 963 of the 1,002 areas. Of the 39 with none, 38 are parts of an area of 2011 that was split and one was made by joining two: section 28 says why, and what the figure is.
- Houses or flats rests on its whole recipe in those 963 areas, and on 75 in 100 in the 39. Every area has a band, as before.
- Against the build of section 29, 202 areas stand in another band of Houses or flats: 101 moved by one band towards Flats and 101 by one towards Houses. None moved by two. No band of any other vibe moved: the measure is a part of no other recipe, and no likeness is counted on it.
- What keeps residents out of a ranking is as it was. A wish for fewer of any group of people draws the notice and changes nothing, on this build as on every other.
- Everything sections 16 to 29 say before you look still stands, but for what they say holds private outdoor space back.

## 32. A preview that holds what homes let for

The catalogue is at version 13, and the engine is 1.14.0. It is the build of section 31 with the list of the high streets beside the rest, as the hosted build names its lists, made once the pipeline read the workbook of the rents of London. The list `m2-living` named the workbook already, and its receipt was in `data/receipts/` since 2026-09-23, so nothing was fetched for it. [ADR 0021](adr/0021-a-price-is-shown-as-the-publisher-gives-it.md), as amended on 2026-09-25, says what is carried and why.

Do everything as section 29 says, with these changes:

| # of section 15 | Run this in its place |
|---|---|
| Before 4 | `uv run python -m burro_pipeline draft --out FOLDER --work FOLDER`, which is the step the hosted build drafts the names with |
| 4 | `make preview ARGS="--release-id lon-2026-09-25-61 --built-at 2026-09-25T08:00:00Z --out data/releases --names FOLDER --list m1 --list m10-health --list m10-land-use --list m11-age-and-households --list m11-high-streets --list m11-outdoor-space --list m12-household-income --list m12-public-transport --list m2-culture --list m2-living --list m2-places --list m2-stations --list m5-journeys"` |
| 5 | `uv run burro-release check data/releases/lon-2026-09-25-61 --receipts data/receipts --income data/releases/lon-2026-09-25-61-income` |
| 6 | The same, with `lon-2026-09-25-61` where section 15 has `lon-2026-09-24-01` |

The draft of names took a minute and a half, and step 4 eight and a half.

What to know before you look:

- The first line reads `inputs=90 missing=3`. Step 4 prints 99 lines of `step=derive status=ok` and five of `step=derive status=skipped`, as in section 31.
- It prints two lines of `step=cost`. The first is of what homes sold for, `rows=2859`, as before. The second is of what homes let for: `source=ons-private-rental-market-london-postcode-district areas=1002 rows=5866 files=4`. Neither holds a rent, a postcode or the name of a postcode district, and nor does `build.json`, which counts the rents under `rent`.
- Step 5 says `99 measures, 641 destinations, 641 places`. The check counts 110,839 facts.
- A rent is of a postcode district or of a whole borough, and never of the area alone. The workbook names 33 boroughs and 329 postcode districts. Of the 1,002 areas, 959 lie in a district by half or more of their homes, and 43 lie in none and take the figures of their borough.
- How many areas take which figure, for each kind of home:

  | Kind of home | Of a postcode district | Of the borough | No figure |
  |---|---|---|---|
  | A room | 284 | 646 | 72 |
  | A studio | 355 | 575 | 72 |
  | One bedroom | 913 | 89 | 0 |
  | Two bedrooms | 932 | 70 | 0 |
  | Three bedrooms | 929 | 72 | 1 |
  | Four bedrooms or more | 663 | 338 | 1 |

- A room and a studio have a range in few districts, so most areas take their borough's. Where the borough has none either the area has no rent for that kind of home, and is ranked with its cost not known.
- Of the 5,866 rows, 3,024 rest on 50 rents or more and 2,842 on 10 to 49. The count is what a page shows, and no word for how sure a figure is.
- It holds no journey time. A journey by public transport to a station is estimated for a search, from distance, and is said to be an estimate.

What a renter is answered, by the rules alone, through the API's test client and with no model:

| The words | What Burro does with them |
|---|---|
| "renting, up to £1,700 a month, leafy" | Applies all of it: renting, a budget of £1,700 a month for one bedroom as a firm limit, and Leafy. It ranks 937 areas and leaves out 65 as over the budget |
| "renting a two bed, max £2,400" | Applies all of it: a budget of £2,400 a month for two bedrooms as a firm limit. It ranks 968 areas and leaves out 34 |
| "somewhere cheap to rent near a park" | Applies nothing. What is cheap is a verdict Burro does not give, and the answer says so. It offers renting and nearer a park, each with no guess, and a budget is for the person to name |

Every sentence of a budget names the place the rent is of, as "in postcode district" and the district, or "in the whole borough of" and the borough. The offer of a budget to rent holds what the publisher advises in its note. No line the service wrote holds a word that was typed, an amount, an id of an area or the name of a borough.

A firm budget of £1,700 a month for one bedroom, held against the middle rent of the place each area lies in:

| | Areas |
|---|---|
| The middle rent is within the budget | 738 |
| It is over the budget by a quarter or less, so the area is kept and ranked lower | 199 |
| It is over by more than a quarter, so the area is left out | 65 |
| Left out, had the limit been held against the upper quartile with no margin | 405 |

The 65 are in seven boroughs: 23 of the 24 areas of Westminster, 20 of the 21 of Kensington and Chelsea, 8 of the 23 of Islington, 7 of the 38 of Wandsworth, 3 of the 30 of Hackney, 3 of the 35 of Lambeth, and the one area of the City of London. No area of the other 26 boroughs is left out.

The tables of the first ten areas of each search name places, so they are kept outside the repository and are in no tracked file.
