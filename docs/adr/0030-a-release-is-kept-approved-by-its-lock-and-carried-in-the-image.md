# 0030. A release is kept in a bucket of its own, approved by its lock, and carried in the image

Status: accepted, 2026-09-25. It says where a release of London is kept and what makes it one that may be served, so it was the founder's to approve, and the founder accepted it the same day: the last section has their words. It applies [0015](0015-where-builds-run-and-what-gates-a-launch.md) and [0018](0018-a-real-release-is-served-with-its-evidence.md), and closes what 0018 left open. Nothing of it has run on a host.

## Context

London had only ever been built on a developer's machine. A hosted run built the made-up city and threw it away. The image of the API copied the made-up city out of the repository, and no release of London could reach it.

- The repository is public. A release holds real figures of real places, so it is never committed, never an artifact of a run and never in a log.
- A hosted run builds on a machine that is thrown away. What it built is lost unless it is kept somewhere.
- The service holds a release to `hashes.json`, which stands beside the release and is signed by nobody. 0018 found that whoever changes a release can change its hashes with it, and asked for a store of approved hashes that is outside the folder.
- The store of publishers' files is a bucket of Cloudflare R2. Its page on API tokens, read on 2026-09-25, gives a token one of four permissions, and holds the two that are of objects to "specific buckets". It names no way to hold a token to a folder inside a bucket. Its page on temporary credentials says that a short-lived credential can be held to "a single bucket" and "optionally to specific paths within the bucket". Such a credential is made from a token, and "cannot exceed the permissions of its parent token".

## Decision

**A release is built twice, kept once, approved by a person, and only then carried.**

| Step | Where | What holds it |
|---|---|---|
| Build | The workflow `data-london`, on two machines, one after the other | Each build reads the store with a key that can only read. It drafts the names of the areas and reads household income from the store, so nothing is handed to it from a machine of a person's own. What the founder decided at the panel it reads from the repository, where the file of changes was published and committed ([0029](0029-a-change-reaches-a-release-through-a-file-of-changes.md)) |
| Compare | The second machine | It holds what it built to the lock of the first build: every file by its hash and its size. If one differs the run ends, and nothing is kept |
| Keep | The second machine, in a bucket of releases | One step is given the key of that bucket, and that key opens nothing else. A file that is kept is never written over |
| Approve | The founder, by a commit | The run shows the lock. To approve the release is to commit the lock under `data/approved/`, named for the release. Nobody else commits one, and no run can: no workflow may write to the repository |
| Take | The step `take`, before an image is built | It takes no release of London but one whose lock is committed, and holds every file to the lock as it copies it out of the bucket |
| Carry | The build of the image | A stage of its own holds what was taken to the lock again, and ends the build where a file differs, is missing, or is not named. The service that runs needs no bucket, no key and no network |

**The lock of a release names every byte of it, and holds no figure.** It holds the id of the release, the commit and the time it was built from, whether it is a preview and a development build, how many areas, measures and vibes it holds, which measures were left out and by which rule, and the hash and the size of every file: of the release, of the folder of its build, and of the folder of household income. The lock of the build's inputs, `lock.json`, is one of those files. So a committed lock fixes what was read as well as what was written.

**A release is kept in a bucket of its own.** A key is held to a bucket and to nothing finer. In a folder of the bucket of publishers' files, the key that writes a release could write a publisher's file, and the key that reads the store to build could read what is kept to be served. So the two are two buckets, and there are three keys.

| Key | Permission at Cloudflare | Bucket | Who holds it |
|---|---|---|---|
| Build | Object Read only | The bucket of publishers' files | The environment `data-london`. The steps that draft and build are given it |
| Keep | Object Read & Write | The bucket of releases | The environment `data-london`. One step is given it, after the two builds were compared |
| Take | Object Read only | The bucket of releases | The founder, for the machine an image is deployed from. It is on no host |

**With no lock, the image carries the made-up city.** The made-up city is committed whole, so it is held to its own manifest and needs no lock. An image is built with it unless a release is named, and the check of every pull request builds it so, with no key.

**What is approved today is a preview and a development build, and its lock says both.** A release that is approved is one that may be carried. Whether it may be shown to the public is not decided here: the gates of 0015 stand as they were. Until the package lockfile is committed, every build is a development build, which 0015 keeps from the public.

What was not taken:

| Way | Why not |
|---|---|
| A folder of the bucket of publishers' files, under another prefix | No token is held to a prefix. The key that keeps a release could then write over a publisher's file, which a lock on the bucket stops for 90 days only |
| A temporary credential held to a prefix | It is made from a token that a workflow would have to hold, and that token is held to the whole bucket. It is one more thing to make on every run, and what it saves is one bucket |
| Fetch the release from the bucket when the machine starts | The service would hold a key and need a network to start. With the bucket down or the key withdrawn it would not start, and a release that was changed would be found only then |
| Fetch the release while the image is built, with a secret of the build | A key would be handed to the builder of the host, and the build would reach a network. The same check is made with no key: the release is taken first, and the build holds it to the lock |
| Have a hosted run build and deploy the image | It needs the host's own program on the runner, which is a new dependency of a workflow, and the host's token in the repository's settings. The image is built as `deploy/README.md` has always said: by the host, when the founder deploys. It is one command more |
| Build twice on one machine | It would need one approval in place of two. It would not show that another machine gives the same bytes, which is what the rehearsal of the made-up city shows |
| Build on two machines side by side, and keep after | Nothing crosses from one job to the next but hashes, so the job that compares holds no release to keep. To keep first and take back is to keep what was never compared |
| Have the run write the lock to the repository | It needs a permission to write that no data workflow has. A lock that a run could commit would approve itself |
| Have the service read the committed lock as it starts | The image is held to the lock when it is built, and nothing changes in an image. It would be a second check of the same bytes. It stays open to add |

## Consequences

- To serve London the founder makes one bucket, three keys and one environment, and stores eight secrets. [The guide to data builds](../data-builds.md), under "London, from the bucket to the service", says each step, and [the guide to deployment](../../deploy/README.md) says how what was approved is served.
- A run of `data-london` asks for two approvals: one before each build is given the key.
- A release that is kept and never approved stays in the bucket, and is served nowhere. Nothing removes it. It is about 90 MB.
- To roll back is to deploy again and name the release before. Its lock is still committed and its files are still kept. To stop a release from being served again, its lock is taken out with `git rm`.
- What 0018 left open is closed for a release that is carried: a name, an outline, which areas are ranked and the sentence of a measure are each in a file that the committed lock names by its hash.
- The key that takes a release is used on the machine the founder deploys from, and the release passes through a folder of that machine that git ignores. The guide says to remove it after.
- The image is about 90 MB larger with London than with the made-up city. Loaded with no socket, on a Mac, the service took 380 MB at its peak with London and 71 MB with the made-up city. The machine in `deploy/api/fly.toml` has 512 MB. That has not been tried on the host.
- A list of files that is added is added to the workflow in the same change, as it is added to the workflow that fetches. A test holds the two together.

## What would change it

- The host offering a token that is held to a prefix. One bucket would then do.
- A workflow being allowed the host's own program. The step `take` and the deploy would then run in a hosted run, and the key that takes a release would be on no machine of a person's own.
- A release too large to carry in an image. It would then be fetched as the machine starts, and the service would hold the committed lock and check each file against it.

## Accepted, 2026-09-25

This record and [0029](0029-a-change-reaches-a-release-through-a-file-of-changes.md) were put to the founder together, as the second of a list of questions: whether the two designs are accepted. These are their words:

> 2. Yes.

Nothing of the design changed with it, and no code did. It is still so that nothing of it has run on a host.
