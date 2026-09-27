/**
 * Site copy for sharing a search, and for a search that was opened from a
 * shared link.
 *
 * It says what a link holds, in words that stay true of the API as the
 * contract describes it: a share is the stored settings of a search under an
 * id made at random, with each place replaced by the station or district
 * that stands in for it unless the sender asks otherwise. Nothing here says
 * anything of a place.
 */

export const SHARE = {
  open: "Share this search",
  holds: {
    title: "What the link holds",
    points: [
      "The link itself holds an id, which is a code that Burro makes at random, and nothing else. This means nobody can tell anything about your search from the link alone.",
      "Burro keeps what you chose in this search under that id, so that the link can open it again. That is whether you are renting, buying or visiting, your budget, the places you want to reach, how much each thing counts, and any area you hid.",
      "Burro does not keep the words you typed, and it does not keep who made the link.",
      "Anyone who has the link can see what you chose and the ranking it leads to, so share it with the people you want to see them.",
      "A link may stop working one day, because Burro keeps only a limited number of them, and because a link made on older data may no longer open.",
    ],
  },
  exact: {
    label: "Share the exact places",
    hint: "If you leave this unticked, Burro replaces each place you named with the station or district that stands in for it. That way the link does not say where you work or study.",
  },
  make: "Make the link",
  makeAgain: "Make a new link",
  making: "Making the link",
  made: "Your link is ready to copy.",
  link: "Link to this search",
  copy: "Copy link",
  copied: "The link has been copied.",
  notCopied: "Your browser would not let Burro copy the link, so the link is selected for you to copy yourself.",
  coarsened:
    "Burro replaced a place you named with the station or district that stands in for it. Because of that, the ranking this link opens may differ a little from yours.",
  exactKept: "The link holds the places exactly as you named them, because you asked for that.",
  /** The box was left unticked, and nothing needed replacing: a station or a district stands in for itself. */
  noneReplaced:
    "Every place in this search is a station or a district already, and those say no more than where they are. Because of that, Burro did not need to replace any of them.",
  noPlaces: "This search names no place to reach, so the link holds none.",
  stored: "What the link holds of the search",
  failed: "The link could not be made.",
} as const;

export const SHARED = {
  pageTitle: "A shared search",
  pageDescription: "Opens a search that someone shared with you.",
  title: "A shared search",
  text: "This search was opened from a link that someone shared. You can change it here as you like, and the link itself will stay as it was.",
  holds:
    "A shared link holds what was chosen in a search, and not what was typed to make it. Each place in it is the station or district that stands in for the place the sender named, unless the sender chose to share the exact places.",
  coarsened:
    "A place in this search is the station or district that stands in for the place the sender named. Because of that, the ranking may differ a little from theirs.",
  exact:
    "The places in this search are the ones the sender named. Either the sender chose to share them, or each one is a station or a district already.",
  stale: "The data has changed since this link was made, so the ranking may differ from what the sender saw.",
  /**
   * After what is said of data that has changed: which version the link was made on, and
   * which the page uses. The name of each follows its line, and a full stop follows the name.
   */
  madeOn: "The link was made on this version of the data:",
  shownOn: "The ranking you see here uses this one:",
  opening: "Burro is opening the shared search.",
  none: {
    title: "This address holds no shared search",
    text: "A link to a shared search ends in an id, and this address has none. This usually means that part of the link was lost, so ask for the link again, or make a search of your own.",
  },
  notOne: {
    title: "This is not a link to a shared search",
    text: "The end of this address is not an id that Burro makes, which usually means that part of the link is missing. Ask for the link again, or make a search of your own.",
  },
  failedTitle: "The shared search could not be opened",
  tryAgain: "Try again",
  /**
   * The way to the search page: where a link opens nothing, and at the end of what says
   * that a search came from a link, since "Start again" there opens the search again as
   * the link holds it.
   */
  own: "Make a search of your own",
} as const;
