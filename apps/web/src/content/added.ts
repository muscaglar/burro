/**
 * What the box says once a search is open and the box holds words the search has read.
 *
 * What is typed then is added to the search. So what is sent to be read is what stands in
 * the box after the words that were read, and never those words a second time: read
 * again, they set back what a person has set by hand since. docs/design/web.md, section 3.
 *
 * Site copy. It names states of the box, and says nothing of a place. Each line is fixed
 * text: it holds nothing of what was typed.
 *
 * It is read between the box and the answer, at a moment when a person does not know why
 * nothing happened. So each line says what Burro did, and then what to do. Once a search is
 * open the settings are behind one fold, which each line names as the fold names itself,
 * and are called what they call themselves: space requirements.
 */

import { REFINE } from "./ways";

/** Where a person goes who would sooner not type: the settings, by their name and the name of the fold that holds them. */
const OR_THE_SETTINGS = `or change your space requirements under ${REFINE.label}.`;

export const ADDED = {
  /** Search was pressed, and nothing stands in the box after what the search has read. */
  nothingNew: `Burro has already read everything in the box. To add to your search, type more after it, ${OR_THE_SETTINGS}`,
  /** The same, where words it had read were changed in the box. Nobody knows what they were, so the change is not read. */
  changed: `Burro only reads what you add at the end of the box, so it has not picked up the change you made to the words before. Type the change at the end of the box, ${OR_THE_SETTINGS}`,
  /** What was added was sent to be read, and words before it had been changed. */
  changedToo: `Burro read what you added, but not the change you made to the words before it, because it only reads what is new. Type the change at the end of the box, ${OR_THE_SETTINGS}`,
  /** What was added was read without the words before it, and words of it were not read. */
  apart:
    "Burro read the words you added on their own, without the words that came before them. Because of that, it helps to say each new thing in full, so that it makes sense by itself.",
} as const;
