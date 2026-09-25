# The releases that are approved

A file here is the lock of one release of London. To commit it to the default branch is to approve that release. Only the founder does.

| | |
|---|---|
| What a lock holds | The id of the release, the commit it was built from, the hash and the size of every file of it, how many areas, measures and vibes it holds, and which measures were left out and by which rule |
| What it never holds | A figure, the name of a place, a key, or the address of a store |
| What it is named | For its release: `lon-2026-10-02-01.json` |
| Where it comes from | The summary of a run of the workflow `data-london`, which shows it once the release was built twice and the two builds were the same |
| What it allows | An image of the API may carry that release, and no other. The build of the image holds every file to the lock, and stops where one differs |
| With no lock here | The image carries the made-up city, which is committed |

A lock is never changed. A release that is wrong is built again under a new id, and has a lock of its own. To stop a release from being served again, take its lock out with `git rm`.

`uv run --no-project python tools/release_lock.py read data/approved/FILE` says what a lock names, and the hash of what it says. The run that built the release shows the same hash.

[The guide to data builds](../../docs/data-builds.md) says how a release is built and approved. [The guide to deployment](../../deploy/README.md) says how it is served.
