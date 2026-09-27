/**
 * Site copy for what Burro does with a sentence, as the two pages that explain say it: the
 * methods in full, and the key to the drawings beside the drawing each sentence is of.
 *
 * Burro takes what it read and asks nothing, so a person who was never asked must be told
 * what was done: that what Burro understood is in the search, that each thing is a chip
 * which can be taken off, and what is left out unless they choose it. Three kinds of
 * thing are left to a person because to count one unasked would come close to a verdict,
 * and whatever Burro cannot tell is left because it does not guess. Both pages name the
 * three in the same words, and give the same reason.
 *
 * When recorded crime counts is said by the one rule, word for word. It names no vibe and
 * no measure: which of them counts recorded crime or who lived somewhere, and which is
 * held to be offered and never applied, is the API's to say.
 */

import { CRIME_RULE } from "./crime";

/** The kinds of thing that are never taken for a person, unless they choose one themselves. */
const NEVER =
  "Some things are left out of your search unless you choose them yourself: anything that counts who lived in an area, recorded crime, and a measurement that closely follows household income.";

/**
 * Why. Burro calls no area the best and ranks places by what is there. A ranking that
 * counted any of these unasked would read as a verdict, on the area or on its people.
 */
const WHY =
  "Burro leaves these to you because it gives no verdict on an area or on the people who live in it, and counting any of them without being asked would come close to one.";

/**
 * What else is left: a wish or a journey that may be somebody else's, and a thing that
 * could count either way where the words give neither. Each is left for one reason.
 */
const ALSO =
  "Burro also leaves a thing out where it cannot tell from your words that you want it yourself, or which way you want it to count, because it does not guess.";

export const TAKEN = {
  /** In the methods: what Burro does with what it read. */
  does:
    "Burro reads what you type and adds what it understood to your search straight away, without asking you to confirm it first. " +
    "Each thing it added appears under the search box as a chip, which is a small label with a cross on it. " +
    "This means you can see what Burro understood, and you can take any chip off again if it is not what you meant.",
  /** In the methods, after it: what is left out, the rule on recorded crime, why, and where Burro says so. */
  never:
    `${NEVER} ${CRIME_RULE} ${WHY} ${ALSO} ` +
    "Whenever Burro has left something out of your search, it names it in a line under the search box and says why.",
  /** In the key, beside the cross of a chip: the same in short, and what the cross does. */
  chip:
    "Burro adds what it understood of your words to your search without asking you first, and shows each thing as a chip with a cross on it. " +
    "The cross takes that thing out of your search again, and Burro then works out the ranking without it.",
  /**
   * In the key, under what a note is: what is left to a person, and why. A row of the key
   * says what it says in a sentence or two, so what Burro cannot tell is said in the methods.
   */
  left: `${NEVER} ${WHY}`,
} as const;
