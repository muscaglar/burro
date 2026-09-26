# How Burro got here

For a reader a year from now. Written on 25 September 2026, the evening Burro was first deployed, from the repository's own record: its history, [the decision records](adr/README.md) and what each guide says of itself. Add to it, and do not rewrite it. Every time is UTC.

## What was built, and in what order

| Day | What was built | Decision records |
|---|---|---|
| 23 September 2026 | [The plan](PLAN.md) and [its research](research/README.md). The licence registry and its gate. The engine, a made-up city to run it on, the API, the website and the source of the iPhone app. The design for [real data](design/london-data.md), and the first files fetched. The review desk. [The legal drafts](legal/README.md) | 0001 to 0017. A model stays at the edges (0002). Nothing typed is stored (0005). Rank places, never residents (0006). A made-up release to build on (0010) |
| 24 September | The first previews of London, of four measures at first. The first draft of its names. Four providers of a model, and none turned on. **The first push, and the first hosted fetch** | 0018 to 0028. A real release is served only with its evidence (0018). Age and households may be ranked on (0006, amended) |
| 25 September | A preview of a hundred measures and fourteen vibes. The panel. The hosted build of London. The guides to [refreshing London](refreshing-london.md) and [adding a city](adding-a-city.md). **The first deploy** | 0029 and 0030. A release is approved by its lock and carried in the image (0030). The proxy audit is dropped (0006, amended) |

## The hosted runs

| When | What |
|---|---|
| 24 September | The first push, and the first hosted fetch into the bucket. The first hosted run of the app's tests failed 47 of them. It was the first time they had been run |
| 25 September, 04:18 | Push. The backend passed. The app failed 4 |
| 13:54 | Push. The backend had one error: a copy of a repository that git was still doing upkeep in. The app failed 5, each over a value that a test held as written and a recording had since changed |
| 18:16 | Push. In the backend a new test started a tool with the hosted runner's own settings in its environment. The app failed 2, both tests older than a change to what is drawn |
| 19:07 | Push. **Every hosted job passed, for the first time** |
| 19:26 | The first hosted build of London was started. Its first build passed in 27 minutes, at the first try |
| About 19:45 | The website was deployed to Vercel and the API to Fly.io, with the made-up city. The website calls the API and no other host |
| 22:48 | The build of London with the traffic near homes was started. It passed whole in 54 minutes, and the release was approved and deployed an hour later |
| 26 September, 00:04 | The website's first build on London asked the API for the page of every area. After about ninety the API's machine fell behind, the host answered 503 for three minutes, and the build failed. The website stayed on the build before. A build now makes the first 24 pages of areas, and any other is made when it is first asked for |

In the runs of 13:54 and 18:16 the test was at fault each time, and no code that is shipped was changed.

## Three kinds of fault that only a hosted run showed

| The fault | How it was closed for good |
|---|---|
| **Git's own upkeep, in the background.** After a commit git looks the repository over in a process it lets go of, and holds a lock meanwhile. A test that copied a repository listed the lock and then found it gone, in some runs only | Every git a test starts is started apart: it does no upkeep of its own, and reads no settings of the machine or of the person. A copy passes over a lock of git's. [conftest.py](../conftest.py), [test_git_is_started_apart.py](../tools/tests/test_git_is_started_apart.py) |
| **A value copied from a recording.** A test of the app held as written an id, a count or a hash that the service had made. Once the answers were recorded again, it held what nothing had made | A test reads such a value from the recording, and a guard fails a file of tests that holds one as written: [RecordedAnswersTests.swift](../apps/ios/BurroKit/Tests/BurroKitTests/Foundation/RecordedAnswersTests.swift) |
| **A hosted runner's settings, reaching a test.** A runner tells every step where its own files are. A tool under test wrote where it was told, so on a runner alone a test opened the runner's own file | What a runner sets is taken out of the environment before any test runs. [conftest.py](../conftest.py), [test_nothing_of_a_runner_reaches_a_test.py](../tools/tests/test_nothing_of_a_runner_reaches_a_test.py) |

[ADR 0020](adr/0020-the-tests-run-side-by-side.md), under "What was found", has each at length.

## What else went wrong, and what it taught

| What went wrong | What it taught |
|---|---|
| Two checks changed the first real build after it was built, to see what noticed. Four things did not | A real release is served only with its evidence beside it, and an image carries one only where its lock is committed. [ADR 0018](adr/0018-a-real-release-is-served-with-its-evidence.md), [ADR 0030](adr/0030-a-release-is-kept-approved-by-its-lock-and-carried-in-the-image.md) |
| No try at Village feel reached the founder's bar. Of the fifty areas each try put highest, 8, 24 and 25 read as villages, where the bar is 30 | A vibe may say that it is less sure than the rest, and is then never taken without a press of its own. [ADR 0013](adr/0013-vibes-are-the-centre.md) |
| The research said another city would reuse the pipeline as it is. Seven of the 43 sources that hold a receipt are London's alone. About a quarter of what the first plan rested on was partly wrong | Have somebody try to refute every claim before it is built on, and list the sources that are one city's own. [Adding a city](adding-a-city.md), section 5 |
| The first rule on logs let a hash of a spec be written. It was tightened twice in a day | A hash can be matched to a workplace by trying specs. Logging is a list of what may be written. [ADR 0011](adr/0011-nothing-is-kept-for-a-search.md) |
| On the first deploy the host's default builder refused to store the image it had built. The host also offers to deploy on every push | The guide names the host's own builder, and no push deploys. [Putting Burro on the internet](../deploy/README.md) |

## What the project would do again, and what it would do otherwise

| Again | Otherwise |
|---|---|
| Build on a made-up city that cannot be taken for a real one. Three parts were built to one contract before any real file was held | Hold the measures against the real city sooner. The plan says that nothing seen on the made-up city says how the product will feel on London |
| Write a decision down with its reason on the day it is made. Thirty records in three days are why this page could be written | Run the hosted checks from the first day. The app's tests were first run a day after they were written, and it took four more pushes to reach no failure |
| Say in every guide what was tried and what was not | Say it in one place. "Never run on a host" stood in many guides, and each went stale in one evening |
| Hold a promise by a test, and say plainly where nothing holds it: [the picture of the whole](architecture.md) | Read from a recording whatever the service made, from the first test |
