# Data builds: what to set up, and how to run one

For the founder. Written 2026-09-23. It applies [ADR 0015](adr/0015-where-builds-run-and-what-gates-a-launch.md) and section 3 of [the plan](design/london-data.md).

No workflow here has run yet. Every time below is an estimate. What only a first run can show is listed in section 12. What was read, and where, is in section 14.

## Where things stand

As of 2026-09-23, on the branch data-m0. Read this first.

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
| The list names the hosts a request may be sent on to, under `may_redirect_to`. The registry entry does not | A change to a list alone can widen where a file may come from | Read a change to `may_redirect_to` as closely as a change to an entry. List m1 names no such host |
| On a host that only the list names, fetch refuses a file only if it came from an address that some entry names. 109 of the 117 entries name no address for their files | A file of one of those entries that is kept on such a host would not be told apart | The same. And name the addresses of an entry's files before a list names a host it shares |
| `seal` puts a file in the lock for any use the gate allows, an internal use included | A file read to validate against is an input of the build | `check` names every row that rests on such a file, under `input_is_allowed`. No figure may rest on it |
| `write_release` asks the gate about the sources a release names, and reads no evidence | A source that is named only in the evidence is not asked about when a release is written | `check` asks about it. Run `check` on every release, with its lock and the registry. Evidence inside a release is for the contract's next schema |
| `check` asks a source behind a journey for `routing`, and one behind a name for `gazetteer` | The weights and the lookup behind a journey must be registered for `routing`, as ADR 0016 has them registered for `scoring`. No entry has been changed for it | The first real build carries no journey. Decide before the first that does |

### What you must do, in order

Steps 1 to 3 are done before the push, with no key and no run. Step 4 is the push. Steps 6 to 12 are done on two websites and on a machine of your own, and none needs a push. Step 13 changes the list, which a run reads on `main`, so it goes with the second push.

| # | Do this | Where it is said how | Time | A push |
|---|---|---|---|---|
| 1 | Read what this branch changed that waits for you, and approve or change it: the third sentence of rule 8 in `AGENTS.md`, the new registry heading and its rules, the use `scoring` on three geography sources, and ADR 0015 and 0016. Six registry entries rest on a permission in writing, and stay gated until you have filed a note of each reply: the plan, task 25 | `docs/adr/0014` to `0016`. `registry/README.md`, "A permission in writing" | 2 hours, the plan's task 11 | No |
| 2 | Finish the first list. Open in a browser each of the seven addresses the list is not sure of. Put right any that is wrong, and name under `may_redirect_to` any other host a download is sent on to. Where an address holds a query, name each of its parameters under `url_parameters`: a list with a parameter it does not name is refused when it is read. Leave each edition and each period under `unsure`: they are stated in step 13, once the file has been read. `uv run python -m burro_pipeline plan --list m1 --words` says what each file still needs. It reads `ready=0` today, and `ready=11` when every file has been read and its edition and its period are stated | `packages/pipeline/src/burro_pipeline/fetch/lists/m1.toml`. Its first lines say which seven, and why | Not known. Nobody has looked | No. It goes with the first push |
| 3 | Run `make ci`. Bring the branch into `main` | | 10 minutes | No |
| 4 | Push the repository to GitHub as a public repository. Turn Actions on | Section 1. The push is yours to make | 1 hour, the plan's task 1 | **The first** |
| 5 | If GitHub refuses the push because of a secret: one test holds the example secret that Amazon prints in its own documentation, to check the signing of requests. It opens nothing. Decide whether it stays. Do not work round the refusal | `packages/pipeline/tests/fetch/test_s3_signing.py` | | |
| 6 | Make the two environments, each with you as its reviewer and `main` as its only branch | Section 2 | 20 minutes | No |
| 7 | Make the bucket, its lock and the fetch key | Section 3 | 25 minutes | No |
| 8 | Store the four made-up secrets of the build | Sections 4 and 5 | 5 minutes | No |
| 9 | Do the rehearsal, and read what the run shows | Sections 5 and 12 | 15 minutes | No. What it shows to be wrong is mended together, in one push |
| 10 | Make a contact address that is not your own, and store the five secrets of the fetch | Section 4 | 10 minutes | No |
| 11 | Start the fetch, for every file of the list. It stores each file and writes no receipt, so the run ends red. That is meant | Section 7 | 5 minutes | No |
| 12 | Save by hand any file that a publisher would not give the runner | Section 7 | Not known | No |
| 13 | Read each file, on a machine of your own. State in the list the edition and the period you found in it | Section 7, "The first fetch of a file writes no receipt" | Not known. No file has been opened as a fetch will store it | It goes with the second push |
| 14 | Start the fetch again. It writes the receipts | Section 7 | 5 minutes | **The second**, before it |
| 15 | Bring the receipts back from the store and commit them | Section 7 | 5 minutes | No. They wait for the next push |

If step 2 is left undone a fetch still runs. Every file is asked for at the address the list holds. A file whose address is wrong ends `status=failed`. Every file that arrives is stored with no receipt, `status=missing why=6`, whether or not step 2 was done.

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
| What you make | Two environments on GitHub. One bucket, one lock and one key at the store. Nine secrets: five for a fetch, and four made-up ones for a build |
| How long it takes | About 1 hour and a quarter, once |
| What it costs | GBP 0 to set up and GBP 0 a month at first. Under GBP 1 a month once the store holds 40 GB (section 11) |
| How many pushes it needs | One, to the first fetch. Three, to the first release you approve |
| How a run starts | By hand, from the Actions page of the website. Never from a push, a pull request or a clock |
| What a run asks of you | One approval. A build of the synthetic release then takes about 10 minutes |
| What a run installs | The pipeline and what it needs: today five packages from outside, and none published after the day its workflow states (section 10) |
| What a run shows | Step names, counts and hashes, under names from a list. Never a row, a key or the address of the store |
| What a run uploads to GitHub | Nothing |

Two workflows exist: `data-fetch` and `data-build`. Today a build builds the synthetic release, which is made up, and reads no store. Section 13 says what is not built.

## 1. Before you start

| You need | Why | Time |
|---|---|---|
| The repository on GitHub, public, with Actions turned on | On a free plan GitHub offers environments for public repositories only (read) | Task 1 of the plan |
| The two workflow files on the default branch, `main` | The "Run workflow" button is shown only for a workflow that is on the default branch (read) | They arrive with the push |
| A Cloudflare account with R2 turned on | The store is an R2 bucket | 10 minutes. Cloudflare may ask for a payment card. That was not read |
| A password manager | Each key is shown once | |

## 2. On GitHub: two environments

About 20 minutes. An environment holds the secrets, and makes a job wait for you.

There are two, so that a build is never given the key that can write a raw file.

| Environment | Used by | Holds |
|---|---|---|
| `data-fetch` | The workflow `data-fetch` | The fetch key |
| `data-build` | The workflow `data-build` | Made-up values, and no key. No step of a build reads the store yet |

Make each one the same way. The names must be exact.

1. Open the repository, then **Settings**, then **Environments**, then **New environment**.
2. Type the name. Press **Configure environment**.
3. Tick **Required reviewers**, and add yourself.
4. Leave **Prevent self-review** unticked. With it ticked you could not approve a run that you started, and you are the only reviewer.
5. Untick **Allow administrators to bypass configured protection rules**.
6. Under **Deployment branches and tags**, choose **Selected branches and tags**, and add one rule: `main`.
7. Save. The secrets come in section 4.

Make both before the first run. If a run names an environment that does not exist, GitHub makes it, with no reviewer, no rule and no secret (read). Such a run is given no secret, because none is stored, but the environment it leaves behind must then be given its rules by hand.

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

When a second person is given write access: protect `main` so that a change needs a review, and keep yourself as the only reviewer of both environments.

### Two settings to check once

| Where | Setting | Set to |
|---|---|---|
| Settings, Actions, General, Workflow permissions | What the run's own token may do | Read repository contents. Each workflow asks for what it needs |
| Settings, Secrets and variables, Actions, Repository secrets | | Put no secret of the store here. A repository secret is given to every workflow, and `ci.yml` runs on pull requests |
| Settings, Secrets and variables, Actions | Debug logging | Store no secret and no variable named `ACTIONS_STEP_DEBUG` or `ACTIONS_RUNNER_DEBUG`. Either turns debug logging on for every run (read) |

## 3. At the store: one bucket, one lock and one key

About 25 minutes. The store is Cloudflare R2, which the plan already names.

### The bucket

1. In Cloudflare, open **R2**, then create a bucket.
2. Name it with a part nobody could guess, such as `burro-raw-` and eight random letters and digits. A name is 3 to 63 lower-case letters, digits and hyphens (read). The name is a secret here, and a run fails any step that prints it. So a plain word such as `raw` would fail steps that printed no secret.
3. Choose a location in Western Europe. Do not set a jurisdiction unless you have decided to: it changes the address.
4. Leave public access off. A bucket is private unless you make it public (read). Never turn on the public address of a bucket, and never give a bucket a domain.

### The lock: what is stored is never deleted or written over

Cloudflare offers four permissions for a key (read). None is named as one that may write and may not delete, and the page does not say whether a key that may write may delete. So take it that the fetch key can. What Cloudflare offers is a lock on the bucket: "Bucket locks prevent the deletion and overwriting of objects in an R2 bucket for a specified period — or indefinitely" (read). A lock holds against every key, the fetch key included.

Make two rules, before the first fetch:

1. Open the bucket, then **Settings**, then the part on bucket locks, then **Add rule**.
2. Name the rule `raw`. Give it the prefix `raw/`. Choose to keep files locked indefinitely. Save.
3. Add a second rule the same way, named `receipts`, with the prefix `receipts/`.

| | |
|---|---|
| What is under `raw/` | Every publisher's file, under its hash |
| What is under `receipts/` | The copy of each receipt |
| What the lock changes for a fetch | Nothing. A fetch asks whether a file is there before it writes, and writes only if nothing is there. It never deletes |
| What the lock stops | A key that has been seen, or a workflow that has been changed, from deleting a file or putting another in its place |
| What the lock does not stop | A new file written under a new name. A key that has been seen can still fill the bucket, and can still read it |
| Who can take a rule off | You, in Cloudflare. The fetch key cannot, as far as was read: to change a bucket's settings is named only under the "Admin" permissions |
| When you would take one off | To delete the files of a source whose licence has ended. Or to put a receipt right, and then the rule `receipts` alone: section 7. Put the rule back the same day |

What was not read, and what a first fetch shows instead:

| Not read | How it is shown |
|---|---|
| Whether a key with "Object Read & Write" may delete a file. The page names "read, write, and list objects", and does not name deleting | Taken here as yes. The lock is what is relied on |
| What the store answers when a locked file is deleted or written over | After the first fetch, try to delete one file in Cloudflare with the rule on. It must be refused |
| Whether a rule made after a file was stored holds that file too | Make the rules before the first fetch, and it does not arise |
| Whether the copy of a receipt can be deleted once the rule `receipts` is taken off, and whether the rule put back holds what was stored before it | The first time a receipt is put right: section 7. Try it once on the receipt of a made-up file |
| Whether a lock costs anything | Section 11 |
| Whether a key can be made that is held to less than "Object Read & Write". Cloudflare names short-lived keys made from a key, "scoped" to less (read). How much less was not read | Not used here |

### The keys

A key here is what Cloudflare calls an R2 API token. It has an id and a secret, and it is held to the buckets you pick. It cannot be held to a folder inside a bucket (read: the page offers "a set of buckets" and nothing finer).

For each: **R2**, then **Manage API tokens**, then create a token, pick the permission, pick **Apply to specific buckets only**, and pick the bucket.

| Key | Make it | Permission at Cloudflare | Buckets | It may | It may not | Kept |
|---|---|---|---|---|---|---|
| Fetch | Now | Object Read & Write | The raw bucket only | Read, write and list files in the raw bucket | Touch any other bucket. Make, change or delete a bucket. Change a lock | In the environment `data-fetch` |
| Reading | On the day you first bring receipts back: section 7 | Object Read only | The raw bucket only | Read and list files in the raw bucket | Write or delete anything. Touch any other bucket | In your password manager, for a machine of your own. Never on GitHub |
| Build | Not yet. When a step of a build reads the store | Object Read only | The raw bucket only | The same as the reading key | The same | It will go in the environment `data-build`, in place of the made-up values |

Cloudflare shows the secret of a key once (read). Put the id, the secret and the address it shows for S3 clients in your password manager before you close the page.

Never make a key with an "Admin" permission for a workflow. An Admin key can delete a bucket, and can take a lock off.

### What comes later, and not today

| When | Make | Why not now |
|---|---|---|
| The first real build, M1 | The build key. A second bucket for what a build writes, and a key that may write to it and to nothing else | No step of a build reads the store, and no code writes a release to it. A key that is used for nothing can only be lost. The second bucket needs two more secrets, which will be named with that code |
| The census block, M4 | A bucket and a key for tables about residents, in an environment of their own | ADR 0015: a product build can never read them |
| The audit, M6 | A bucket and a key for the audit, in an environment of their own | The same |
| Any time | A second copy of the raw bucket in another account | The plan, section 14, row 18. It is not set up by anything here |

The plan speaks of three buckets. It needs one more than that, because a key cannot be held to a folder: the raw files and what a build writes must be in two buckets for the build's key to be unable to write a raw file.

## 4. The secrets, by name

About 15 minutes. The four names of the store go in each environment. A fetch has one more.

| Name | What it is | In `data-fetch` | In `data-build` |
|---|---|---|---|
| `BURRO_STORE_ENDPOINT` | The address Cloudflare shows for S3 clients, whole, beginning `https://` | The real one | A made-up one: `https://rehearsal-0000.invalid` |
| `BURRO_STORE_BUCKET` | The name of the raw bucket | The real one | A made-up one: `rehearsal-bucket-0000` |
| `BURRO_STORE_KEY_ID` | The id of a key | The real one, of the fetch key | A made-up one: `rehearsal-key-id-0000` |
| `BURRO_STORE_SECRET` | The secret of a key | The real one, of the fetch key | A made-up one: `rehearsal-secret-0000` |
| `BURRO_FETCH_CONTACT` | An email address, or an `https://` page, where a publisher can reach Burro | The real one | No |

Open **Settings**, **Environments**, the environment, then add each under **Environment secrets**.

**The build holds made-up values, and no key.** No step of a build reads the store yet, so a build is given nothing that opens it. The step "Every secret is set" of a build refuses a value that could be real: the address must end `.invalid`, which no host can, and every other value must begin `rehearsal-`. The day a step of a build reads the store, its workflow changes, and this table changes with it. A test holds the two together.

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

Every build after this one is a rehearsal too: it checks the made-up values and hides what is made from them, as a fetch does with real ones.

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

### Bring the receipts back

A figure is cited to a receipt, and `seal` reads receipts from the repository. After a fetch in a run, on a machine of your own that holds the reading key:

```
uv run python -m burro_pipeline receipts
git add data/receipts
```

It writes each receipt under `data/receipts/`, and never writes over one that is there. Its first line says which kind of store it was given, and must read `step=store kind=object_store`. Its last line reads `step=store status=ok receipts=... new=...`. Then commit them, if you have said yes to decision 2 of the plan. They go with your next push: nothing waits for them until a lock is sealed. The step's own `--help` says how the store is named on a machine of your own.

### Put a receipt right

The first receipt of a file stands, in the repository and in the store. No run puts a receipt right: a run that finds a receipt which says something else than the list ends `status=differs`, and writes over nothing. That is what keeps a run from dropping a receipt without a word. So a receipt that is wrong is put right by hand.

| | |
|---|---|
| Who | You, and nobody else. It needs the right to change a lock at the store, which no key of a workflow has, and the right to commit to `main` |
| When | The receipt states an edition or a period that the file itself does not bear out. Nothing else in a receipt is put right this way: a file with another hash is another file, with a receipt of its own |
| What is never touched | The file under `raw/`. Its rule stays on throughout, and the file is the one that was stored first |

1. Bring the receipts back. If the wrong receipt is not yet in the repository, commit it as it is. The history then holds what was wrong.
2. Put the list right: state the edition and the period as the file has them.
3. Take the wrong receipt out of the folder with `git rm`, in a commit that holds this and the change to the list, and nothing else. Write in its message the file id, which of the edition and the period was wrong, what the receipt said, what the file says, and the day the copy in the store is deleted.
4. Push.
5. In Cloudflare, take the rule `receipts` off. Delete the one copy: it is under `receipts/`, then the id of the source, and is named for the file id. Put the rule back the same day. The rule `raw` is never taken off for this.
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

`uv run python -m burro_pipeline describe` prints the names in a file's own layout: its columns, its sheets, its layers. Run it on a machine of your own that holds the reading key, before the code that reads the file is written.

- **What it prints is for your own machine, and never for a public log.** It takes the first row of a table for the names of its columns. Where a table has no header, that row is data: a name, a postcode, a price. So treat all it prints as if it held a row.
- **No workflow runs it.** The rules check refuses a workflow that does. If it were run behind the public log, every line of it would be withheld.
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
| `kind=object_store` | Which kind of store a step was given. In a run it never reads `kind=folder` | A word from a fixed list |
| `kind=html` | What arrived in place of a file, where it was not kept | A word from a fixed list |
| `host=...` | A host a request was sent on to: the first twelve digits of a hash of its name, and never the name | Twelve digits of a hash |
| `why=3` | Why a file was not fetched, or has no receipt | A number of one or two digits |
| `http=403` | The status a publisher answered with | Three digits |
| `file_id=...`, `release=...`, `file=...`, `copy=a` | A file by its id, a release by its id, a file of a release, one of the two builds | The shape of each, or a name from a fixed list |
| `manifest_sha256=...`, `sha256=...` | Hashes | 64 digits of a hash |
| `fact_has_a_row=2`, `gate_refuses=1` | How many findings a rule made. The name is the rule's | A whole number |
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

If a key may have been seen: look in Cloudflare at what is in the bucket and when it changed. A fetch key can read every file and write new ones. With the lock on, it cannot delete a file or put another in its place. With the lock off, it can do both. A reading key can only read.

If the address of the store may have been seen: it holds the account's id, which cannot be changed. An address alone opens nothing, because the bucket is private and every request needs a key. Rotate every key, delete the logs of that run on its page, and write down what happened.

### What a run installs

A job that holds a key installs only what a step imports. Every job installs with one line, named "Install", and the rules check allows that line and no other.

| | |
|---|---|
| What it installs | The pipeline and the ranking engine, which are this repository's own, and what they need from outside: today `pydantic` and the four packages it needs |
| What it leaves out | The development group: the API, the test runner and what they need. With it, an install brings 26 packages from outside, as counted on 2026-09-23 |
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
- It trusts the five packages, and the ones a build needs, as they stood on the day stated.
- It does not look outside the repository. The installer also reads a settings file from the folders above the one it runs in, and from the settings folder of whoever runs it (read, in its help). No step of a run can write one there. What the hosted runner holds there has not been seen.
- It does not hold the release of Python. `.python-version` names 3.13, and which release of 3.13 a run is given is not held.

### Move the day

| | |
|---|---|
| Who moves it | You, or whoever writes the code, in a change that you read before you approve the next run |
| When | When a change to the code needs a newer version of a package. When a fault is found in a package that a run installs, and a newer version mends it. Otherwise leave it: an old day costs nothing |
| Where it is written | Once in `tools/check_data_workflows.py`, as `PACKAGES_BEFORE`, and on the line named "Install" of each job that installs: two in each data workflow |
| What it costs | One change, and one push. It can wait for a push you are making anyway |

1. Choose a day that has come. A test refuses a day that has not: it would hold nothing back.
2. Change `PACKAGES_BEFORE`, and the same day on the four lines. `make ci` fails until all five agree.
3. See what the new day brings before you push:

   ```
   uv tree --package burro-pipeline --no-dev --exclude-newer DAY
   ```

   Write the day as the check writes it. The command reads the package index, and writes a lockfile that git ignores. Read the versions it lists against the ones a run installed last. An index that does not say when a file was uploaded has every file refused: then leave this step out, and read the step "Install" of the next run in its place.
4. Commit it with a line that says why the day moved. It goes with your next push.
5. In the first run after it, read the step "Install". If it fails, a package has no version as old as the day: choose a later day.

### Move the version of the installer

Seldom. It is written once in `tools/check_data_workflows.py`, as `INSTALLER`, and on the line `version:` of each job of a data workflow: three in `data-fetch`, four in `data-build`. `make ci` fails until all eight agree. `ci.yml` names its own, and is not held to it. Before the change, read the help of the new version for the words the line that installs uses, against row "The help of `uv`" of section 14. It is one change and one push, and can wait for a push you are making anyway.

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

## 13. What is not built yet

| Not built | Why | Until then |
|---|---|---|
| Sending a release to the store | No code writes a release to the store. The store's code keeps raw files only | The build workflow builds, compares and throws away. A release is on no machine after a run |
| The full log of a step, kept in the store | The same | A failure is found on made-up data: section 9 |
| Bringing a receipt from a run into the repository | A fetch writes the receipt to the runner's disk, and the runner is thrown away. So the fetch also keeps a copy in the store. To reach the repository from there, a person brings it back, or the run shows it, or the run pushes it. The second shows more than step names, counts and hashes. The third needs a permission to write that no data workflow has. The plan's decision 2, on committing receipts in public, is also open | A person brings the receipts back and commits them: section 7. It needs a key on a machine of your own. Whether that is acceptable is yours to decide |
| Bringing a lock and a report from a run into the repository | The same. To approve a release is to commit its lock, and a lock sealed in a run is on a disk that is thrown away | No workflow seals a lock yet. `seal` is run on a machine of your own |
| Showing the shape of a fetched file in a run | The plan's fastest route to M1 has the first fetch print each file's sheet and column names. Those are not step names, counts or hashes, and where a table has no header they are a row. So a run withholds them, and no workflow runs it | `uv run python -m burro_pipeline describe` on a machine of your own that holds the reading key: section 7 |
| A check, inside a run, that the environment has a reviewer and a branch rule | GitHub gives an environment's rules to anyone who may read the repository (read), so the first job could ask and refuse to go on. It was left out because the answer's shape has not been seen, and a check that is wrong would stop every run | You watch for the wait: section 2 |
| A build from a committed lockfile | The lockfile is not committed yet: ADR 0008 says when it will be | Every build is a development build, and is never served. A run holds its packages to a day, and not to a hash: section 10 |
| A fetch of only the files the store does not hold | A fetch asks the publisher for every file it is given, stored or not | To fetch again what failed, start a run for each item, or one for the whole list |
| A receipt written from the store, with nothing asked of the publisher again | The same. The second run of a file asks its publisher for it again, to write the receipt | Every file is fetched twice: section 7 |
| The hash of the file that was read, held in the list | A list holds no hash. So nothing but `new=0` on the line of the second run shows that the receipt is of the file that was read | Read `new=` on each line of the second run: section 7 |
| A record of a correction that a step reads | A receipt is put right by hand, and the record is the history of the repository. No step checks it | Section 7, "Put a receipt right" |
| Workflows for routing and for research with a model | Later milestones | |
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
