# 0020. The tests run side by side

Status: accepted, 2026-09-24. The founder decided that the tests run side by side, and that one library may be added for it. The limit is a default, taken on 2026-09-25: it is the founder's to overturn.

## Context

The whole suite was to stay under 30 seconds. Joined with the first builds of London it holds some 11,000 tests, and in one process it took 56 to 61 seconds. No test is slow. Half of them take a thousandth of a second or less, four take more than one second, and the slowest takes under four. There are many of them, and each new measure adds more.

A smaller sample of every generated test would buy the time back once, and the suite would grow past the limit again.

## Decision

1. `make ci`, and so hosted CI, runs the tests in several processes at once, with `make test-split`. It starts one process for each core, and `JOBS=4` sets another number. A hosted runner has four cores.
2. One library is added to the development group for it: `pytest-xdist`, which runs pytest's tests in several processes. It brings `execnet`, the one package it needs. Both are pure Python, as [ADR 0008](0008-package-sources.md) asks: each is one wheel for any platform, holds no compiled file and installs no command.
3. The tests are split by file. The tests of one file run in one process, in the order the file gives them. Some 45 files make something once for all their tests: a release, a repository, a filled desk, a build from real files. Split test by test, every process that was handed one of a file's tests would make it again.
4. `make test` runs the tests plainly, in one process: `make test ARGS="-k name"`. It is how one test is run, and it is what `-x`, `-s` and a debugger need.
5. A test counts on nothing that another test left behind, and leaves nothing behind itself. It asks for port 0 and is told which port it was given. It writes under the temporary folder pytest gives it. It puts back what it set that outlives it: the environment, the level of a logger, an attribute of a module.
6. The first two of those are held by `conftest.py` at the root, and not by luck. A test that binds a port of its own choosing, or opens a file to write or makes a folder at a path of its own, fails every time it runs, alone or beside others, and is told the port or the path. It may bind again a port it was given, as a test does that stops a server and starts it again. It may write under a name the system made up for it, through `tempfile`: no two are the same.

## What was found

One test was found that leaned on another, and one that leaned on the clock. Once the first was mended the suite was run side by side 30 times without the store of fetched files, over four, eight and sixteen processes, and once with it. No run failed. The second showed itself later, in one run of seven. Once both were mended `make ci` was run ten times more, and then three at once, twice. No run failed.

- A test of what a log may hold passed only when no test before it, in its process, had started the service. The service sets the level of its own logger when it starts, and only the root logger was put back after a test. In one process the order of the files hid it. Every logger's level is now put back.
- A test that builds the same layers twice, and holds what is written to the same bytes, failed in some runs only. A zip holds the time each member was written, to two seconds, and the made-up zips it reads were written at the time of the clock. Two builds that fell either side of such a second read other files. The zips are now written at one time. It leaned on no other test, so one process would have shown it as well as many: more runs showed it.
- A third was found on 2026-09-25, by a hosted run and by none before it. A test was handed a copy of a repository that git was still at work in. After a commit git looks the repository over in a process it lets go of, which holds a lock there for as long as it looks, and the copy listed the lock and then found it gone. It leaned on no other test either. Git is now started to do no upkeep of its own and to read no settings of the machine or of the person, by `conftest.py` at the root, in the environment of whatever starts it. A copy of a repository passes over a lock of git's, and still fails on any other file that is gone.
- A fourth was found the same day, by the next hosted run and by none before it. A runner tells every step where its own files are, in the environment: what a step writes to one is shown on the page of the run, or handed to another job. The tool that writes the lock of a release writes to two of them where they are named, and its tests started it with whatever they were handed. So on a runner, and nowhere else, a test opened the runner's own file to write. What holds the rule refused it, in each case that ran one of the two commands that write there. The tool took the refusal for a fault nobody foresaw, as it is made to take any, and so four of those cases failed as well. A program that a test starts is not heard by what holds the rule, and would have written there unseen. `conftest.py` at the root now takes out of the environment what a runner sets, before any test runs: every variable whose name begins `GITHUB_`, `RUNNER_` or `ACTIONS_`, and `CI`. A test of what a tool does on a runner names a file under its own folder, as the tests of that tool now do. Where pytest reads `CI` it says a failure in full, and those lines are what a hosted run says again where anyone can read them. So what the runner set `CI` to is put back while pytest sums up, when every test has run, and at no other time.

No test was found that binds a fixed port, writes a fixed path or reads a file that another test wrote. Every file a run opens to write, every folder it makes and every port it binds was written down and read: some 40,000 files, 57,000 folders and 400 binds.

Two careless tests were then planted in two files each, one that binds a fixed port and one that writes a fixed path. Before there was anything to hold the rule, one of the four failed in one run of five, where it met its like, and all four passed in the other runs. With it, all four failed in seven runs of seven, and nothing else did.

## What was measured

On 2026-09-24, in seconds, three runs each:

| Processes | The tests alone | `make ci` whole |
|---|---|---|
| 4 | 28, 34, 41 | 39, 46, 56 |
| 8 | 24, 38, 39 | 35, 52, 54 |
| 16 | 28, 30, 28 | 43, 45, 45 |

The time of a run moved more from one run to the next than with the number of processes, so no one figure here is to be leaned on. Of 29 runs over four processes, the tests took from 26 to 52 seconds in 28, and 80 in one. Over sixteen they took from 20 to 27 in ten runs. In one process they took from 56 to 115.

More than four processes buys little. Every process reads all the tests before it runs its share, and the slowest file takes some ten seconds whichever process runs it.

On 2026-09-25 the suite held some 19,000 tests. On a hosted runner, which has four cores, `make ci` whole took 135 seconds in the morning, 252 and 169 in the afternoon, and 289 in the evening.

The same day, on a developer's machine with other work running beside them, the tests alone took 78, 104 and 101 seconds with one process for each core, and 104 and 141 over four. What many tests read was then made once for them. After that they took 82, 82 and 135 seconds, and 91 and 95 over four. The work they do, in seconds of a processor's time, fell from between 665 and 830 to between 579 and 628, and over four processes from between 357 and 420 to between 322 and 338. So the work fell by between a tenth and a quarter. The time by the clock fell over four processes. With one process for each core it is not seen to have fallen. Both moved with what ran beside the tests. The rest of `make ci` took 38 seconds, of which the type check took 31.

## The rule

A whole run of `make ci` on a hosted runner stays under five minutes. The tests alone stay under two minutes on a machine of a developer's own, run as `make ci` runs them, where nothing else is running. A generated test draws a fixed sample in `make ci` and runs in full under the marker `full`. `AGENTS.md` states it.

It is a default. The founder was asked three times which limit stands, and had not said. So on 2026-09-25 the default was taken, and work was not held up for an answer. It is the founder's to overturn.

The limit was 30 seconds, for the tests in one process, and a minute over four processes was then proposed. Neither had been so for some days.

The limit is met, and not by much. The run of the evening of 2026-09-25 took 289 seconds, which is 96 in 100 of five minutes, and the four runs of that day took from 135 to 289. So a run that is over the limit says little of the change it came with. On a developer's machine one run of six took more than two minutes, with other work running beside it. Nothing more was built to bring either time down: what would is said below.

No test and no check holds the limit: a person reads how long a run took. The job `ci` of the hosted workflow is stopped after ten minutes. That is for a run that hangs, and is of the whole job with what it installs. It is not the limit.

## Consequences

- A test that leans on another now fails where it passed before, and fails in some runs only. It is mended. It is never run again until it passes.
- Within a file the order of the tests is kept. Between files there is no order.
- What a test prints is shown only if it fails, and a debugger cannot be used. `make test` is for both.
- One file is never split, so a file that takes longer than its share sets the least time a run can take. Where the store of fetched files is named, one file of tests on real files takes four and a half minutes, and the whole suite took five and a half over four processes.
- One test starts the review desk again on the port it had, as a person would. Another process could be given that port in between. It was not seen in any run, and the test is left as it is.
- What holds the rule hears what Python itself opens and binds, in the process that runs the test. It does not see what a program started by a test does, a database opened by its path, or a file that is renamed into place. It costs about a third of a second of a processor's time in a whole run.
- No lockfile is committed yet (ADR 0008), so hosted CI installs the newest `pytest-xdist` from 3.6 up.

## What would change it

The founder naming another limit. The numbers stand in the rule above and in `AGENTS.md`, and in no test and no check, so the two are changed in one change and nothing else is.

A run of `make ci` taking more than five minutes on a hosted runner, or the tests alone more than two on a developer's machine where nothing else is running. Then, in this order:

1. Look for a file of the folder store under its hash, and not through the whole store. The change was written, and with it the tests did about a fifth less work, in the one run that was made. It was left out on 2026-09-25, because it is not the store as it stands in every case. It hands a file over where the store as it stands refuses: from a store that holds a link that leads nowhere, from a folder that may be passed through and not listed, and from the folder of a hash that is written in capitals, on a disk that takes capitals and small letters for the same. In no case does it hand over other bytes than were asked for. Whether those cases may change is the founder's to say.
2. Run the type check in a job of its own, beside the tests. On a developer's machine it is between a fifth and a quarter of a run of `make ci`.
3. Split the slowest file in two. It is 6 in 100 of the work of the tests, so it buys little today.
4. Give the generated tests a smaller sample.
5. Only then raise the limit.
