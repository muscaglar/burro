/**
 * Site copy for what Burro counts in every search that nobody chose.
 *
 * A result says that its fit is based on so many things that count, and a person who asked
 * for four of them could not tell what the rest were. They are the settings a search starts
 * from. The settings name them, where a person looks for them and can change them: in a
 * sentence at their head, and on the bar of the group that holds each.
 *
 * Every name is the API's, from the meta route, and none is written here. It is written for
 * somebody who has never seen Burro: in whole sentences, which say what follows from what.
 */

/** True where the names are of one thing alone. */
const one = (names: readonly string[]) => names.length === 1;

/** Several names as a person says a list. The names are the API's and are said as they came. */
const LIST = new Intl.ListFormat("en-GB", { style: "long", type: "conjunction" });

const listed = (names: readonly string[]) => LIST.format(names);

export const USUAL = {
  /**
   * On the bar of a group, beside what a person asked for: what the group holds that Burro
   * counts in every search. It is said as "Not counted" is said of what a person took off.
   */
  onTheBar: (names: string) => `Counted in every search: ${names}`,
  /** Before a search. Nothing is ranked yet, so nothing is said of how much each counts. */
  before: (names: readonly string[]) =>
    one(names)
      ? `Burro already takes one everyday thing into account in every search: ${listed(names)}. ` +
        "You can turn it up, down or off in its group below."
      : `Burro already takes a few everyday things into account in every search: ${listed(names)}. ` +
        "You can turn each of them up, down or off in its group below.",
  /**
   * Once a search is open, where each of them counts for half as much as the least of what
   * was asked for, or for less. It is said only where that is so.
   */
  little: (names: readonly string[]) =>
    one(names)
      ? `Burro also takes one everyday thing into account in every search: ${listed(names)}. ` +
        "It counts for much less than the things you asked for, and you can turn it up, down or off in its group below."
      : `Burro also takes a few everyday things into account in every search: ${listed(names)}. ` +
        "Each of them counts for much less than the things you asked for, and you can turn each one up, down " +
        "or off in its group below.",
  /** Once a search is open, where one of them counts for as much as something that was asked for. */
  also: (names: readonly string[]) =>
    one(names)
      ? `Burro also takes one everyday thing into account in every search: ${listed(names)}. ` +
        "You can turn it up, down or off in its group below."
      : `Burro also takes a few everyday things into account in every search: ${listed(names)}. ` +
        "You can turn each of them up, down or off in its group below.",
  /** Once a search is open in which nothing was asked for, as when the settings are ranked as they stand. */
  alone: (names: readonly string[]) =>
    one(names)
      ? `You have not asked for anything yet, so Burro has ranked the areas by the one everyday thing that it ` +
        `takes into account in every search: ${listed(names)}. You can turn it up, down or off in its group below.`
      : `You have not asked for anything yet, so Burro has ranked the areas by a few everyday things that it ` +
        `takes into account in every search: ${listed(names)}. You can turn each of them up, down or off in ` +
        "its group below.",
} as const;
