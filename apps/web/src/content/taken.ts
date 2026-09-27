/**
 * Site copy for what Burro does with a sentence, as the two pages that explain say it: the
 * methods in full, and the key to the drawings beside the drawing each sentence is of.
 *
 * Burro takes what it read and asks nothing, so a person who was never asked must be told
 * what was done: that what Burro understood is in the search, that each thing is a chip
 * which can be taken off, and that two kinds of thing are never taken for them. Both pages
 * name those two in the same words, and give the same reason.
 *
 * When recorded crime counts is said by the one rule, word for word. It names no vibe and
 * no measure: which of them counts recorded crime, or who lived somewhere, is the API's to
 * say.
 */

import { CRIME_RULE } from "./crime";

/** The two kinds of thing that are never taken for a person. */
const NEVER =
  "Two kinds of thing are always left out unless you choose them yourself: recorded crime, and anything that counts who lived in an area.";

/**
 * Why. Burro calls no area the best and ranks places by what is there. A ranking that
 * counted either of these unasked would read as a verdict, on the area or on its people.
 */
const WHY =
  "Burro leaves these to you because it gives no verdict on an area or on the people who live in it, and counting either of them without being asked would come close to one.";

export const TAKEN = {
  /** In the methods: what Burro does with what it read. */
  does:
    "Burro reads what you type and adds what it understood to your search straight away, without asking you to confirm it first. " +
    "Each thing it added appears under the search box as a chip, which is a small label with a cross on it. " +
    "This means you can see what Burro understood, and you can take any chip off again if it is not what you meant.",
  /** In the methods, after it: what is never taken, the rule on recorded crime, where Burro says so, and why. */
  never:
    `${NEVER} ${CRIME_RULE} When Burro notices one of them in your words and leaves it out, ` +
    `it names it in a line under the search box. ${WHY}`,
  /** In the key, beside the cross of a chip: the same in short, and what the cross does. */
  chip:
    "Burro adds what it understood of your words to your search without asking you first, and shows each thing as a chip with a cross on it. " +
    "The cross takes that thing out of your search again, and Burro then works out the ranking without it.",
  /** In the key, under what a note is: what is never taken, and why. */
  left: `${NEVER} ${WHY}`,
} as const;
