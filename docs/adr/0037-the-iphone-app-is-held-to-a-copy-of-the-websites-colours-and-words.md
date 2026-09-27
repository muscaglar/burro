# 0037. The iPhone app is held to a copy of the website's colours and words, until it is given the look

Status: accepted, 2026-09-26, as a default that was taken so that the website could be given its look. It is the founder's to overturn. **Nobody has run the app's tests since**: the last section says what that leaves unproved.

## Context

The iPhone app is the same product as the website. Its check, the hosted job `ios`, held it to the website in three ways:

| The check said | By reading |
|---|---|
| That the app's models and routes are the contract's | `contracts/openapi.json` |
| That the app is tested on what the service answered | `apps/web/test/recorded/`, copied byte for byte |
| That the app's colours and words are the website's | `apps/web/src/styles/tokens.css`, every file of `apps/web/src/content/`, and three files that say how a source is credited |

The website was then given a look of its own ([0033](0033-the-website-looks-like-the-map-of-a-gentle-game.md)): twenty colours by name, one look where there were two, a light and a dark, and new words beside the old. The app is not given the look now. Held to the website as it changed, the app's check would have failed at the first colour.

## Decision

**The app's colours and words are held to a copy of the website's files, kept in the app, as those files stood on 2026-09-26, until the app is given the look.**

| Matter | What is so |
|---|---|
| The copy | `apps/ios/website/`: 27 files, laid out as `apps/web/src` is. `styles/tokens.css`, every `.ts` file of `content/`, `SourceLine.tsx`, `SourceNote.tsx` and `lib/facts.ts`. Each is the website's file of that day, byte for byte |
| What reads it | The app's generator, which makes the app's tokens from it, and the app's tests, which hold its words to it. No file of the app's check reads `apps/web/src` |
| What it is not | It is not the website. Nothing in `apps/web` reads it, and nothing in it follows `apps/web`. No file of it is edited, and none is added |
| What the check still says of the service | All that it said: that the app's models are made from the contract as it stands, that its recorded answers are the website's byte for byte, and that three lines of [the contract](../design/contract.md) are said word for word |
| What the check no longer says | That the app's colours and words are the website's. It says that they are the copy's |
| When the app is given the look | The generator and the tests are pointed at `apps/web` again, the copy is taken out, and the app's colours and words are brought to the website's as they then stand. [The app's guide](../../apps/ios/AGENTS.md#the-websites-look-and-words) has the two names to change |

What was weighed, and put aside:

| Way | Why not |
|---|---|
| Give the app the look in the same build | The look was settled on the website, in a browser, in a day. The app has been seen on no screen yet |
| Keep the app's check on the website, and let it fail until the app follows | A check that fails for a known reason is soon not read, and the app's other promises are held by the same job |
| Take the tests of colours and words out of the app | They hold the app's words to words that were reviewed. The copy keeps that |
| Keep a copy of the tokens alone | The words were as much the website's. A word of the app is the copy's, word for word, or its test lists it as the app's own |

## Consequences

- **The app and the website may now show other colours and say other words for the same answer, and no check says so.** Since the copy was taken the website has changed three lines of the words it holds, which said "the settings below" and say "the settings", has written its statement of accessibility again, and has gained six files of words that the app has none of.
- **Later that day the website's words were written again, and where things stand on its search page was changed**, once the founder had walked it ([0038](0038-the-words-of-the-website-are-written-for-a-person-who-has-never-seen-burro.md), [0035](0035-the-search-page-is-one-box-and-the-look-gives-way-to-the-answer.md) as amended). The copy holds the words as they were before. The app has no tab to begin a search at, its settings are where they were, and its way to compare is where the website's was. Nothing of the app was changed for it, and no check says that the two differ.
- **The app has none of the look**: no ground, no box, no drawing, no rabbit, and the faces of the system. [The design of the website](../design/web.md) describes the look from its section 8 on, and the app is built to the rest of it.
- **The app follows the search of the website event for event**, and that did not change. The website's box now sends what was added to a search and no more ([0036](0036-the-box-sends-what-was-added-and-keeps-counts.md)). The app's does not.
- **A recording that is added for the website is copied to the app** by `make -C apps/ios generate`, as before. Twelve were added on 2026-09-26, and the app's copy was made again.
- Nothing stops a new test of the app from reading `apps/web/src` again. No test refuses it.

## What is not proved

| Not proved | What stands in its place |
|---|---|
| **That the app's tests pass.** No test of the app has been run since the copy was made | `make -C apps/ios generate-check` passes. Every file the tests now read is byte for byte the file they read before. The only Swift that changed is eleven names of a path, one new name, and comments |
| That the app compiles for iOS | The package and its tests compile for macOS, with a warning treated as an error |

The first push runs the job `ios`, and it is the first thing to read after one. `make -C apps/ios check`, on a Mac whose Xcode can run `swift test`, says the same.

## What would change it

| If | Then |
|---|---|
| The app is given the look | As the decision says. This record then describes history |
| The founder wants the app to follow the website's words now, and its colours later | The tests of words are pointed at `apps/web/src/content` again, and the copy keeps `styles/tokens.css` alone |
| The job `ios` fails on the first push | It is mended before anything else of the app is changed: the copy was made so that it would not |
