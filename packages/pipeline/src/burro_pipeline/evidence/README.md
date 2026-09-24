# Evidence

Nothing is said about a place unless a stored record stands behind it ([ADR 0014](../../../../../docs/adr/0014-evidence-first-and-census-figures-shown.md)). This folder holds those records, the lock a build is made from, the coverage report, and the rule that no fact is served without evidence. It is built to sections 4, 6, 7 and 8 of [the pipeline design](../../../../../docs/design/london-data-pipeline.md), as [the plan](../../../../../docs/design/london-data.md) joined it to the other designs.

Every example below is made up, and every test runs offline on made-up files.

## The records

| Record | One for each | What it is for | Module |
|---|---|---|---|
| Receipt | File of a publisher | Says what was fetched, from where, when, and under which registry entry. Every other record names a file by its `file_id` | `receipt.py` |
| Method | Way of working a figure out | Holds the sentence the methods page prints. Every parameter must stand in the sentence | `method.py` |
| Evidence row | Figure, and figure that is missing | Says which files a figure rests on, by which method, how much of the area was covered, and in which state that leaves it. The row of a measure or of a tag holds the figure too. Its key is the `fact_id` | `row.py` |
| Claim | Thing a model helped to find | Not yet used. It waits for milestone M8, on quotations: build nothing on it until then. Holds a publisher's own words, the receipt of the page, and where in the page the words stand. The model is recorded as how the claim was found, and is never a source | `claim.py` |

Every record is frozen and refuses a field it does not know. `canonical()` gives the one form it is written in, which is how a release file is written too. `digest()` is the SHA-256 of that form. A record that fails to validate is said with `in_words(error)`, which says where and why and never what it was given. Never print the error itself.

`Evidence` in `store.py` is the evidence of one release: its receipts, methods, rows and claims in one document. It cannot be made with a loose end. A row that names a method or a file the document does not hold is refused.

### A receipt

```json
{
  "file_id": "f-7f2e7a5fec5d",
  "source_id": "synthetic",
  "use": "scoring",
  "publisher_file": "made-up-parks.gpkg",
  "members": [],
  "url": "",
  "sha256": "7f2e7a5fec5df5160fea8700df1b0fd1a0bb43bb7915a3b01eace45d20b81f57",
  "bytes": 68,
  "retrieved_at": "2026-09-23T09:12:31Z",
  "how": "made_up",
  "edition": "made up",
  "data_period": {
    "as_at": "2025-04",
    "start": null,
    "end": null
  },
  "geography": "polygon",
  "licence_evidence": null
}
```

- `how` is `fetched`, `by_hand` or `made_up`. A made-up file cites the source `synthetic` and has no address. Nothing else may.
- `url` is an https address with no login, key or fragment. `clean_url` takes them out. A key written into the path cannot be told from the path, so the step that fetches must clean such an address itself.
- `listed_url` is the address the list gave for the file, before any redirect, as clean as `url`. A receipt that has none leaves the field out, as the example does: one written before the field, one of a file saved by hand whose list gives no address, and one of a made-up file.
- `edition_from` says where the edition was read, when no page of the publisher states one: `where`, which is `xml_header`, `geopackage`, `street_extract` or `retrieved`, the place in the file as `at`, and whether the period of the data was read there too. A receipt of an edition that a page stated leaves the field out, as the example does. The day a GeoPackage was last changed is about the file, and is never the period of its data.
- `taken` says which part of the file was taken, where fetch took part of one: the size of the whole file, the box the rows were wanted in and the column that holds it, the columns taken, which row groups of how many, and the runs of bytes that were kept, each as its first byte and how many. `sha256` and `bytes` are then of the part, which is those runs one after another. A receipt of a whole file leaves the field out, as the example does.
- `geography` is null until it has been read from the file. It is never assumed.
- The file is kept in the vault at `vault_key()`, which is `raw/<source_id>/<sha256>/<publisher_file>`. The receipt is kept in git at `path()`, which is `data/receipts/<source_id>/<file_id>.json`. Fetch keeps a copy of it in the vault at `kept_key()`, which is `receipts/<source_id>/<file_id>.json`, because a hosted run writes to a disk that is thrown away.
- Fetch writes receipts and no other part does. It imports this record, and its store works out a key with the same function the receipt uses. A test holds both to it.

### A method

```json
{
  "derivation_id": "walk_to_nearest@1",
  "sentence": "The walk from homes to the nearest park of 2 hectares or more, taken as the median by homes and rounded to 10 metres.",
  "kind": "measured",
  "parameters": {
    "hectares": 2,
    "rounded_to_metres": 10
  },
  "code": "burro_pipeline.derive.walk"
}
```

The number after `@` rises when the arithmetic changes. `kind` is `measured`, `modelled` or `averaged`. The commit of the code is in the lock, not here.

`code` is a module of the pipeline or of core. `check` looks for it on disk and refuses a method whose module is not there. The module this example names is not built, so `check` would refuse it.

### An evidence row

```json
{
  "fact_id": "syn-n0001/feature/park_proximity",
  "derivation_id": "walk_to_nearest@1",
  "inputs": [
    "f-4dd9152af428",
    "f-7f2e7a5fec5d"
  ],
  "data_period": {
    "as_at": null,
    "start": "2021-03-21",
    "end": "2025-04-30"
  },
  "retrieved_on": "2026-09-23",
  "units_used": 10,
  "units_expected": 11,
  "weight_covered": 0.97,
  "state": "partial",
  "flags": [
    "unit_split"
  ],
  "value": 290.0
}
```

`value` is the figure as the release gives it: the value of a measure, or the score of a tag. It is null in a row with no figure, and in the row of a label, an outline, a cost, a journey or a station, which is not one number. `check` holds the release to it, so a figure that is changed after the build is found.

A row is in one of seven states. There is no blank.

| State | Meaning | Counted as a gap |
|---|---|---|
| `present` | A value, with at least 99% covered | No |
| `partial` | A value, with less covered. The share is shown | No |
| `below_threshold` | Too little covered. The value is null | Yes |
| `source_gap` | The source holds nothing for the area | Yes |
| `suppressed` | The publisher withheld it | Yes |
| `not_published` | The publisher does not publish it for areas this small | No. It is said once |
| `not_carried` | This build does not work the measure out. `build.json` says why, where a reason is known | Yes |

### A claim

Not yet used. It waits for milestone M8, on quotations: build nothing on it until then. The record of a release keeps a list of claims, and the report counts them. No release holds one.

A claim has many fields, so its example is not printed here. It is `CLAIM` in `packages/pipeline/tests/evidence/examples.py`, beside the three above. It quotes a made-up page about a made-up area.

`rests_on(text)` says whether the quote is in the page's text as written, at the place the claim gives. There is no near match. The ten checks of the research design, the word lists and the second look are not here: they belong to the research part.

## From a screen back to a file

This is one figure of the synthetic release, traced with the evidence `made_up.py` makes for it. The release is made up and so is the file. In a real release the same steps end at a publisher's file, with its address, its edition and the time it was fetched.

| Step | What is there |
|---|---|
| 1. The screen | On the page of Alderwick: "Straight-line distance to the nearest marked way into a park of 2 ha or more: 970 m, closer than 33% of the 21 areas compared in this release." |
| 2. The fact | `facts_for` in core gives the sentence its fact, `syn-n0001/feature/park_proximity`, which cites the source `synthetic` as of 2025 |
| 3. The evidence row | `evidence.row("syn-n0001/feature/park_proximity")`: state `present`, 10 of 10 units, all of the area covered, retrieved on 2026-09-23 |
| 4. The method | The row's `derivation_id` is `made_up@1`: "Made up for testing from the invented character of each area, and it measures nothing." |
| 5. The files | The row's `inputs` are `f-4dd9152af428` and `f-bca3e23cf453`. `evidence.receipt(...)` gives `made-up-homes.csv` and `made-up-measures.csv`, each with its hash, its period and `how: made_up` |
| 6. The vault | The second file is kept at `raw/synthetic/bca3e23cf453e625eb758e8a68902557ab2a3475a8f53d0dd36b6ca10a055aa8/made-up-measures.csv`. A made-up file is in no vault, so here the trace ends |
| 7. The lock | The lock of the build names both files by hash. `Lock.admit` refuses any bytes it does not name |

Three kinds of fact depend on what a person asks, so each rests on a row that does not: a journey on `<area>/travel/<mode>`, a `budget_fit` on the row of its cost, and a `missing` on the row of the area's name. `evidence_key` gives the row for any of these.

Two kinds of fact are counted from the figures of measures, and hold no figure of their own. A vibe that an area cannot be placed on says the area's name and how many parts of the recipe have a figure, so it rests on the row of the name and on the row of each such part. A likeness rests on the row of each measure the two areas were compared on, in both areas. `rows_behind` gives the rows for any fact. A vibe that is placed has a row of its own, which holds its score.

## What is kept out of the product

A table about residents is read by the audit, or shown as the statistics office's own table on an area's page. It is used for nothing else (ADR 0006 and 0014). The licence gate allows such a file, for that one use. Fetch keeps none today, because no store is built for one (`why=15`), and it will once there is. So the gate alone does not keep such a file out of a build. Three rules do, and each has a test.

| Where | What is refused | Rule |
|---|---|---|
| `seal` | The receipt of such a file. No lock is written | `file_is_for_the_product` |
| `check`, of every row | A row of evidence that rests on such a file | `input_is_for_the_product` |
| `check`, of every fact | A fact that is served from such a row | `evidence_is_for_the_product` |

A file is kept out when any of these holds:

- its receipt says it was fetched for `audit_only` or for `census_table`
- the registry holds its source under the heading `audit` or `residents`
- the registry holds its source for `audit_only` or for `census_table`, under any heading.

Nor may a row rest on a file whose source the registry does not hold, because nothing shows that such a file is not kept out: `source_is_registered`.

## What the registry does not allow for a use

The gate lets a file be read for less than a release does with it. A `gated` or `held` source may be read to validate against or for a prototype, and a share-alike source may be approved for routing and for nothing else. Fetch keeps such a file, and `seal` puts it in the lock. So `check` asks the gate again, of every file a row rests on, for the use the figure is put to (ADR 0016):

| Row of | The use that is asked for |
|---|---|
| A name or a boundary | `gazetteer` |
| A feature, a tag or a cost | `scoring` |
| The journeys of a mode | `routing` |
| A station | `display` |

A row is named under `input_is_allowed` when a file it rests on was fetched for an internal use, or comes from a source the gate refuses for that use. It is named whether or not it holds a figure. A file that was read to validate against may stay in the lock, with no row resting on it.

A source that a file of the release cites is asked about too, for the use of that file, where no row put to that use rests on a file of the source. The source of a place to reach is one: no row stands behind a place, so `places.json` is asked about, for `destination_search`. The file of the release is then named, under the same rule. Where a row does rest on a file of the source, the row is what is asked about and what is named, so one fault is found once. The registry is asked as it stands on the day of the check: a source can be gated, or lose a use, after a release was built.

`fence.py` holds the rule, and `seal` and `check` both ask it. A file fetched for `validation_only` may be sealed, because the checks of a build read it.

Every lock is the lock of a product release. The step that makes the census table, and the audit, are not built. Neither will read this lock.

## The lock

`seal` writes the lock before a build starts: every input by hash, the commit of the code, and the hash of the package lockfile.

It takes the list of the build, which is the list the files were fetched from, and holds the folder of receipts to it. A list holds no hash, because it is written before a file is fetched. So a receipt is held to what fetch copies from the list into it: the source, the use, the edition and the period. Where the list names several files of one source, edition and period, they are counted: as many receipts as files, each of a file with a name of its own. A receipt of an edition that is no longer listed is moved out of the folder before a build is sealed. It stays in the history of the repository.

### A file that states its own edition

A publisher that replaces a file under one address leaves the list no edition to state. The list says where the file states its own, and fetch writes the receipt from what it reads there. So the folder may hold several receipts of one file of the list, one for each edition that was fetched. Which one a build takes is a rule, and `take` in `lock.py` is the one place that applies it:

| | The rule |
|---|---|
| Which receipts are of the file | Those fetch could have written from the item of the list: the item's source and use, the list's own address for the file, the place the list says the edition is read in, and an edition that is the list's words and then a day or a time. Where the file gives the edition alone, the period is the list's, and the receipt gives that too |
| Which one is taken | The edition the build is told to take with `--edition ITEM=EDITION`, written as the receipt writes it. Told nothing, the newest: the one whose edition states the latest day. The day is the one the file states, and never the day the file was retrieved |
| What the lock says | Beside the hash of the file, `item` and `edition`: the name the list gives the file, and the edition that was taken. An input whose edition the list states has neither field, and is written as it was before them |
| What is passed over | The receipts of the other editions. They are no part of the build, and are not refused as receipts the list does not name |

So the lock alone says what was read. A build that is given the editions a lock names seals that lock again, byte for byte, whatever has arrived since. For a file that holds no date the edition is the day it was first retrieved, so the lock of a build that takes one holds that day.

The lock names the code by its commit. In a repository `seal` reads the commit that is checked out, and refuses a working copy with changes. It reads git's own files and runs no program, because no module of the pipeline may run one: `repository.py`. It reads `HEAD` and its branch, the commit, the index and every tracked file. A working copy is clean when every tracked file hashes to what the index says of it, and the tree the index describes is the tree of the commit. A file that git does not track is not looked at. A file that git changes on its way in, as a setting for line endings does, reads as changed.

The repository is looked for as git looks for it: in the folder `--root` names, and in every folder above it. So `seal` run in `packages/` reads the same commit, and refuses the same changes, as `seal` run at the top. What stands nearest is what is read: a `.git` that holds no repository is refused, and nothing above it is tried in its place. Only where no folder above holds a repository can nothing be read, and the commit is taken as it is given.

The step is not run for a real build without `--list`. `seal` looks at the code first, and then stops at the first file that may not be in the lock:

| Stops when | Rule |
|---|---|
| The working copy holds changes that are not committed: a tracked file is not as the index has it, or something is staged | `tree_has_no_changes` |
| A commit is given, and it is not the one that is checked out | `commit_is_checked_out` |
| The repository cannot be read | `repository_is_read` |
| No folder above holds a repository to read, and no commit is given | `commit_is_named` |
| The licence gate refuses the source for the use its receipt gives. The gate is asked about every file before anything else is asked of one | `gate_refuses` |
| A real build is sealed with no registry | `real_build_needs_a_registry` |
| The file is kept for the audit or for the census table. The licence gate allows such a file for that one use, so it is the lock that keeps it out of a build | `file_is_for_the_product` |
| A file the list names has no receipt in the folder | `listed_file_has_a_receipt` |
| A receipt is in the folder that the list does not name | `receipt_is_listed` |
| Two receipts are of a file of one name, source, edition and period. Or two receipts of one file that states its own edition state the same edition: one edition is one file | `listed_file_has_one_receipt` |
| An edition is named with `--edition`, and no receipt of the file states it. Or it is named for what is no file of the list that states its own edition | `named_edition_has_a_receipt` |
| The vault's listing lacks a file, or gives it another size | `file_is_in_the_vault` |
| A receipt names licence evidence that is not in `registry/evidence/` | `licence_evidence_is_saved` |
| Two receipts name one file | `one_receipt_for_a_file` |
| There is nothing to seal, and the release is not made up | `lock_has_an_input` |
| A made-up file is an input of a real release, or a real file of a made-up one | `made_up_is_consistent` |

A build reads nothing the lock does not name. `Lock.admit(content)` and `Lock.admit_file(path)` hash what they are handed and refuse it if the hash is not there. A lock with no package lockfile is a development build, which is never served.

## Reading a file in a build

A step that works a figure out never opens a file by its path. It asks `Inputs.open` in `burro_pipeline/inputs.py` for a source and a use, and is handed a checked copy of the file with its receipt. `Inputs.opened` is every file a step was handed, which is what a row of evidence names as its inputs. Nothing is written to the store.

| Stops when | Rule |
|---|---|
| The licence gate refuses the source for the use the step puts the file to. The use may differ from the one the file was fetched for | `gate_refuses` |
| The file is kept for the audit or for the census table | `file_is_for_the_product` |
| No receipt is there for what the step asked for, or more than one | `input_has_one_receipt` |
| The copy taken from the store is not the size and the hash its receipt gives | `file_is_in_the_vault` |
| The build has a lock, and the lock does not name the file by that hash | `input_is_locked` |
| The file is not laid out as the step was written to read it: a column is missing, a code is not a code, an outline is not a shape. The refusal says which in fixed words, and repeats nothing from the file | `input_is_as_described` |

The step `preview` leaves a measure out of a release, and goes on, in four cases. Each is said on the line of `derive`, by the name of its rule, and in the file `build.json` beside the release. Nothing is filled in for a measure that is left out.

| Left out when | Rule |
|---|---|
| The file of the measure has no receipt among those of the list | `input_has_one_receipt` |
| A check of the measure's figures found that they do not yet say what the measure is named for. Its module says what was found, under `HELD_BACK`. It is left out whatever core says of it | `measure_is_not_held_back` |
| The row of the catalogue the measure makes does not name and measure it as core does. Core would refuse the release | `measure_is_as_core_says` |
| No area has a figure for the measure | `measure_has_a_figure` |

A build with no lock is a development build, which is never served.

## Coverage

`cover(release, evidence, homes)` gives one cell for every area and every measure: its state, how much was covered, and whether a row of evidence stands behind it. `report` writes the five tables a person reads: by source, by measure, by area, the gaps, and the claims. `summary` gives the counts a build may print.

- Where a row stands behind a cell and agrees with the release, the cell takes the row's state. Where none does, the state is worked out from the release alone and the cell says `record: false`.
- A share of the whole is a share of homes only when `homes` is given. Otherwise every area counts once, and the report says so. No count of homes is made up.
- The report of the synthetic release is committed in `packages/pipeline/tests/evidence/fixtures/`. `make fixture` writes it again, and a test fails when it is stale.

## No fact without evidence

`unevidenced(release, evidence, lock, registry)` names every fact of a release that has no record behind it. It asks core for the facts, so it sees what the API would serve. A release is fit to serve only when it returns nothing.

| Finding | Meaning |
|---|---|
| `fact_has_a_row` | A fact is served, and no row stands behind it |
| `row_has_a_value` | A fact is served, and its row says there is no figure |
| `row_holds_the_figure` | A figure or a score is served that is not the one its row holds |
| `row_holds_the_coverage` | The release says a share of the area stands behind a figure, or a share of the recipe behind a tag, that is not the one its row holds |
| `percentile_is_cores` | A measure is served with a place among the areas that is not the one core works out from the figures of the release. An area is ranked on it |
| `tag_is_cores` | The release holds a tag with a raw value, a score or a share of its recipe that is not the one core works out from the measures of the release |
| `source_has_a_file` | A fact cites a source, and its row rests on no file from that source |
| `input_is_locked` | A row rests on a file that is not in the lock |
| `input_is_for_the_product` | A row rests on a file kept for the audit or for the census table |
| `evidence_is_for_the_product` | A fact is served, and its row rests on such a file |
| `lock_is_for_the_product` | The lock holds a file whose source is kept for the audit or for the census table |
| `method_is_found` | A method names a module that is not in the pipeline or in core |
| `source_is_registered` | A row rests on a file whose source is not in the licence registry, or the lock holds such a file |
| `input_is_allowed` | A row rests on a file that the registry does not allow for the use its figure is put to, or that was fetched for an internal use. Or a file of the release cites a source that the registry does not allow for the use of the file, and no row put to that use rests on a file of the source |
| `row_has_a_fact` | A row says there is a figure, and the release holds none |
| `credit_is_the_registrys` | The release names, credits or licenses a source otherwise than the licence registry does |
| `receipt_is_the_locked_file` | A receipt in the evidence gives another hash or size than the lock gives the file. The id of a file is the first twelve digits of its hash, so the whole hash is compared |
| `receipt_is_as_committed` | A receipt in the evidence is not the receipt that was committed for its file |
| `evidence_is_of_this_release` | The evidence or the lock was written for another release |
| `row_names_its_method` | The row of a measure names another method than the one the code works it out by, or the row of a tag another than the method of a tag |
| `row_rests_on_its_file` | The row of a measure does not rest on the one file the code reads it from. Where the publisher cuts the product to squares of the grid, the row may rest on the file of each of several squares, and on no other file of the source. Where the publisher gives a file for each part of the whole, as the food hygiene register gives one for each authority, the row rests on the file of every part that the lock names. The row of a tag rests on the files of the measures of its recipe that have a figure in its area |

The last two are found where the check is told what the code says stands behind each measure and each tag, which `preview` and `burro-release check` tell it. Two measures may cite one source, and only this tells the evidence of one from the evidence of the other. The step `check` is not told, because it is run on evidence that was made elsewhere. `receipt_is_as_committed` is found where the check is given the receipts that were committed: `preview` gives it those of the build, and `burro-release check` takes `--receipts`.

`check` stops before it looks at a fact when it is not given what it needs:

| Stops when | Rule |
|---|---|
| A release that is not made up is checked with no lock. A made-up release is built from no file, so its lock may be left out | `real_release_needs_a_lock` |
| A release that is not made up is checked with no licence registry. The registry says which files are kept for the audit or for the census table | `real_release_needs_a_registry` |
| A release that is not made up is checked with no hashes of its build | `real_release_needs_its_hashes` |
| The manifest, the evidence or the lock is not as the hashes of the build say, or the hashes are of another release | `build_is_as_it_was_written` |

## The hashes of a build

`preview` writes `hashes.json` beside the release: the SHA-256 of its manifest, of its evidence and of its lock. The manifest holds the hash of every file of the release, so the three fix every byte that was built. `Hashes` in core is the record.

A release that is not made up is served only while all three are as they were written. `open_served` in core holds them, and the API and `burro-release check` both open a release through it. `check` holds them too. So a figure that is changed after the build is refused, and so is evidence that is changed and still well formed.

To approve a release is to commit its lock and its hashes. Until a release is approved nothing outside the build's own folder holds its hashes, so a person who changes a release can change its hashes with it. `burro-release check` then still holds every figure to its row of evidence.

## Commands

```
uv run python -m burro_pipeline seal --release-id ID --built-at TIME --list LIST --vault-listing FILE
uv run python -m burro_pipeline check FOLDER --evidence FILE --lock FILE --hashes FILE [--registry PATH] [--list FILE]
uv run python -m burro_pipeline coverage FOLDER --evidence FILE --out REPORT [--homes FILE] [--json FILE] [--build FILE]
```

Each takes `--made-up` in place of real inputs, for the synthetic release. Each says what it reads and writes under `--help`, with examples. They are three of the steps of the pipeline's one command line: `uv run python -m burro_pipeline --help` lists them all.

What a command prints may be read by anyone. On standard output it prints one line of `key=value` pairs, which is the form `tools/public_log.py` lets through to a public log:

```
step=check status=ok release=syn-2026-09-23-01 facts=1119 rows=1225 files=6 findings=0 evidence_sha256=...
```

Why a step was refused is said in words on standard error, which a public log withholds. A refusal of the lock is one line: what is wrong, what a person can do about it, and the rule's name. Neither ever holds a row, a key, the address of the vault, or the name of an area. Which facts `check` found goes to the file `--list` names.

## Not here yet

| What | Why |
|---|---|
| `evidence.json` and `coverage.json` inside a release | The contract must change first. Core refuses a release folder that holds a file it does not know. They stand in the folder beside the release, and a release that is not made up is not served without that folder |
| A figure in the row of a label, an outline, a cost, a journey or a station | None of them is one number. The hashes of the build hold them, and nothing else does |
| `evidence.json` as two lists, one of what is the same for every area | It is a saving of size. Rows are written whole until the contract fixes the form |
| A refusal to seal with no list, in the function `seal` itself | The step `seal` is not run for a real build without `--list`. The function still seals what it is given when it is given no list, because two tests of fetch call it so |
| A refusal to seal outside a repository | A commit that is given there cannot be checked. The walk and the tests of fetch seal in a folder that is in no repository |
| Files that git does not track | Which of them git ignores is for git to say, and no module of the pipeline may run a program. A file that is not tracked and not ignored does not stop a lock |
| Licence evidence that a registry condition asks for | A condition is free text. `seal` checks the evidence a receipt names, and cannot tell that one should have been named |
| Telling apart two files of one source, edition and period | A list holds no hash, and a receipt does not say which item of a list it is of. Such files are counted, and each must have a name of its own. The first list has three |
| A receipt for a file the build makes, such as a crosswalk | A row names the publisher's files a crosswalk was made from |
| The launch gates | They are the founder's to confirm. The report counts what they would read |
