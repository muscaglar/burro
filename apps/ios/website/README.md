# The website, as the app is held to it

A copy of every file of `apps/web/src` that the check of the iPhone app read for colours or for words, as each stood on 2026-09-26. It is laid out as `apps/web` is, so `src/content/search.ts` here is the copy of `apps/web/src/content/search.ts`.

The app's tokens are generated from `src/styles/tokens.css`, and the app's tests hold its words to the rest. The three files of tests under `src/content` are here because the check reads every `.ts` file of that folder. Nothing runs them.

This is not the website. To change the website, change `apps/web`: nothing there reads this folder, and nothing here follows it. No file of the copy is edited, and none is added to it. [The app's guide](../AGENTS.md#the-websites-look-and-words) says why the copy is kept, and what to do when the app is given the look.
