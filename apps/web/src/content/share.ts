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
      "The link holds an id made at random, and nothing else. The id says nothing about your search.",
      "Burro keeps the settings of this search under that id: renting or buying, the budget, the places to reach, what counts, and any area you hid.",
      "It does not keep what you typed, and it does not keep who made the link.",
      "Anyone who has the link can see those settings, and the ranking they give.",
      "A link may stop working. Burro keeps only so many, and one made on older data may no longer open.",
    ],
  },
  exact: {
    label: "Share the exact places",
    hint: "Left unticked, each place you named is replaced by the station or district that stands in for it, so that the link does not say where you work or study.",
  },
  make: "Make the link",
  makeAgain: "Make a new link",
  making: "Making the link",
  made: "The link is made.",
  link: "Link to this search",
  copy: "Copy link",
  copied: "Link copied.",
  notCopied: "The link could not be copied. It is selected: copy it yourself.",
  coarsened:
    "A place you named was replaced by the station or district that stands in for it. The ranking from this link may differ a little from yours.",
  exactKept: "The link holds the places as you named them.",
  /** The box was left unticked, and nothing needed replacing: a station or a district stands in for itself. */
  noneReplaced:
    "No place needed replacing: each place in this search is a station or a district already, which says no more than where it is.",
  noPlaces: "This search names no place, so the link holds none.",
  stored: "The settings the link holds",
  standIn: (position: number) => `Place ${position}, by the station or district that stands in for it`,
  failed: "The link could not be made.",
} as const;

export const SHARED = {
  pageTitle: "A shared search",
  pageDescription: "Opens a search that someone shared with you.",
  title: "A shared search",
  text: "This search was opened from a link. Changing it here does not change the link.",
  holds:
    "A shared link holds the settings of a search, and not what was typed. Each place in it is the station or district that stands in for the place the sender named, unless the sender chose to share the exact places.",
  coarsened:
    "A place in this search is the station or district that stands in for the place the sender named. The ranking may differ a little from theirs.",
  exact:
    "The places in this search are the ones the sender named: they chose to share them, or each is a station or a district already.",
  stale: "The data has changed since this link was made, so the ranking may differ from what the sender saw.",
  madeOn: "It was made on data release",
  shownOn: "It is shown on",
  opening: "Opening the shared search",
  none: {
    title: "No shared search in this address",
    text: "A link to a shared search ends in an id. This address has none. Ask for the link again, or make a search of your own.",
  },
  notOne: {
    title: "This is not a link to a shared search",
    text: "The end of this address is not an id Burro makes. Part of the link may be missing. Ask for it again, or make a search of your own.",
  },
  failedTitle: "The shared search could not be opened",
  tryAgain: "Try again",
  own: "Make a search of your own",
} as const;
