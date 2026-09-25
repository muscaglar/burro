# 0020. The tests run side by side

Status: accepted, 2026-09-24. The founder decided that the tests run side by side, and that one library may be added for it. The limit of a minute is proposed in place of 30 seconds, and is left to confirm.

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

What the tests take on a hosted runner has not been measured.

## The rule

The tests of `make ci` stay under a minute over four processes, where nothing else is running. `AGENTS.md` states it. It is about four processes because that is what hosted CI has. Of 29 runs over four processes, one took longer, and 23 took more than 30 seconds.

The limit was 30 seconds, for the tests in one process. A minute is proposed in its place, and the founder has not yet said so: it is to be confirmed, or put back to 30, once a hosted run has given a figure.

## Consequences

- A test that leans on another now fails where it passed before, and fails in some runs only. It is mended. It is never run again until it passes.
- Within a file the order of the tests is kept. Between files there is no order.
- What a test prints is shown only if it fails, and a debugger cannot be used. `make test` is for both.
- One file is never split, so a file that takes longer than its share sets the least time a run can take. Where the store of fetched files is named, one file of tests on real files takes four and a half minutes, and the whole suite took five and a half over four processes.
- One test starts the review desk again on the port it had, as a person would. Another process could be given that port in between. It was not seen in any run, and the test is left as it is.
- What holds the rule hears what Python itself opens and binds, in the process that runs the test. It does not see what a program started by a test does, a database opened by its path, or a file that is renamed into place. It costs about a third of a second of a processor's time in a whole run.
- No lockfile is committed yet (ADR 0008), so hosted CI installs the newest `pytest-xdist` from 3.6 up.

## What would change it

The tests of `make ci` taking more than a minute on a hosted runner. Then, in this order: split the slowest file in two, give the generated tests a smaller sample, and only then raise the limit.
