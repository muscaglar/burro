# 0015. Builds run in hosted CI from a private store, and a release is gated before launch

Status: accepted in part, 2026-09-23. The founder has decided where builds run. What may be committed, and the numbers on the launch gates, follow the plan's recommendations and are the founder's to confirm (decisions 2 and 12 of [the plan](../design/london-data.md)). Amended the same day, for the founder to confirm: a copy of each receipt is kept in the store. Amended again the same day, to apply [0007](0007-no-solicitor.md) as it now stands: the rail schedule waits on its subscription and its agreement, and on no reply.

## Context

[0014](0014-evidence-first-and-census-figures-shown.md) asks for real, cited data for all of London. Until now no dataset had been downloaded.

- The repository is public. Anyone can read the log of a workflow, and what it uploads. A cache can be read from a pull request.
- Some publishers' files hold rows about one home or one person: sales, the food register, the schools register. Some licences end on breach.
- A release must repeat. The same inputs, built again, give the same bytes.
- Hosted CI costs nothing for a public repository, as its provider's page read on 2026-09-23. A runner is a fresh machine for every run.

The detail is in [the plan](../design/london-data.md), section 3, and in [the pipeline design](../design/london-data-pipeline.md), sections 6 to 8 and 12.

## Decision

### Where the work runs

| Work | Runs | May reach |
|---|---|---|
| Writing and testing code | Anywhere, on small made-up files shaped like the publishers' | Nothing |
| Fetch | Hosted CI on this repository | The publishers' hosts, and the store |
| A file a publisher will not give a runner | A person, in a browser. Its receipt says `by_hand` | |
| Every step of a build after fetch | Hosted CI | The store only |
| Routing | Hosted CI if the benchmark shows it fits a runner. If not, a machine rented for the hours of the run | Nothing |
| Research with a model | Hosted CI, in a workflow of its own, before a build | The publisher and the model's providers |

- Every data workflow is started by hand, on the default branch, in an environment the founder must approve. None runs on a pull request, so a pull request never meets a key.
- The gate comes first. `Registry.require(id, use)` is called before a file is fetched, again when a build's inputs are sealed, and again when a release is written.
- A build never calls a model. Nothing asks a model about a place while a person waits.
- The rail schedule is not fetched to a runner or to the store until its subscription is approved and the agreement as executed has been read. If the agreement holds the data to the UK, as the public copy of it does, the schedule is held and worked on in the UK.

### The private store

- Every publisher's file is kept as it was fetched, under its hash, and is never written over.
- The store has three parts, each with a key of its own: the product, the census tables about residents, and the audit. The key of a product build cannot read the other two, and cannot write a raw file. Only fetch can.
- The address of the store and its keys are secrets. They are in no file of this repository, no log and no receipt. Code reads them from the environment.
- A copy of each receipt is kept in the store beside its file, under `receipts/`. Fetch runs on a machine that is thrown away, and a receipt written only to its disk would be lost with it. The first copy kept stands. The receipt a build reads is still the one in the repository: a person brings the copies back with the step `receipts`, and commits them. The other two ways to get a receipt out of a run were not taken: to print it shows more than step names, counts and hashes, and to push it needs a permission to write that no data workflow has.

### What a run may print, upload and commit

| | Rule |
|---|---|
| Printed | Step names, counts, hashes and timings, from a list of what may be printed. Never a row, a key or the address of the store. The full log goes to the store |
| Uploaded by CI | No raw file, working table, matrix, release or rejected claim is ever an artifact, a cache entry or a release asset |
| Committed | Receipts, locks, reports and the curated gazetteer files. They hold the addresses of publishers' files, hashes, dates, counts and codes, and no row of data. A coverage report names real areas that have gaps. To confirm: decision 2 |

Before the first real file is fetched, a canary row is planted in a made-up file, and the public log and everything the run uploaded are searched for it. A second canary sits in a row that makes a parser fail, so that the error path is searched too.

### What gates a launch

A release is served to the public only when every line below holds.

| Gate | Passes when |
|---|---|
| Honest for every area | Every area has a name, a boundary, travel times, a cost range, and enough of what is measured to be ranked (0014). The numbers are in the next table |
| Evidence | Every fact has an evidence row. Every file a row names is in the lock and in the store |
| A build of record | Built from a committed lockfile ([0008](0008-package-sources.md)), from a clean tree at a named commit, twice, and the two manifests are the same byte for byte |
| Licences | `make registry-check ARGS=--strict` passes: every credit is confirmed and nothing is left to settle. On 2026-09-23 it lists 37 items. No source that is gated, held or banned is in the release |
| The checks | Every check of the pipeline design, section 8 |
| A person | The founder has read the coverage report, the diff and the validation report, and approves the release by committing its lock and its reports |

Until the lockfile is committed every build is a development build. A development build is never served to the public.

The numbers, proposed. To confirm: decision 12.

| Gate | Passes when |
|---|---|
| Every home in one area | Every output area of London is in exactly one area. Every live London postcode finds one area |
| Travel times | Every area has a time, or "beyond the cutoff", to at least 99% of destinations, by every mode |
| Cost range | Every rankable area has a rent range and a price range, for at least one kind of home. Where no rent is published for a borough, a price range alone, if the founder agrees (decision 7) |
| Each measure | A value in at least 95% of rankable areas, or the release carries the measure as not rankable |
| Enough to rank | Proposed as "80% of measures in every rankable area and none under 60%". This reads two ways. It is not a gate until the founder has stated it |

A release with gaps that are said on the screen may go to closed testers before launch. It does not go to the public.

## Consequences

- Nothing is kept on a runner, so everything a build needs is in the store or in git.
- Bringing receipts back needs a key to the store on a machine that a person runs. A lock sealed in a run has the same trouble, and no workflow seals one yet.
- Whoever writes the code cannot read why a run failed: the public log holds counts, and the full log is in the store. The plan's section 14, row 2, is still open.
- Which country a runner is in is not known. So the rail schedule goes to no runner unless its agreement allows it.
- The store is one place to lose everything. A second copy is the plan's section 14, row 18.
- The first fetch cannot run until the founder has pushed the repository, made the approved environment and the store, and stored the secrets.
- The store is the only running cost: under GBP 1 a month by the plan's estimate, which is not measured.

## What would change it

- Routing that does not fit a runner. The build then uses a rented machine, which this record already allows.
- Publishers that refuse a runner for most files. Fetch would move to a machine that a person runs.
- A row, a key or the address of the store found in a public log. Every data workflow stops until the cause is fixed.
- Hosted CI no longer free for this repository.
