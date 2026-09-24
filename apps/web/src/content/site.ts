/**
 * Site copy for the shell: the words every page carries.
 *
 * Site copy names controls, states and codes. It never holds a number or a
 * proper noun about a place: those come from the API.
 */

export const SITE = {
  name: "Burro",
  description:
    "Describe the life you want and name the places you need to reach. " +
    "Burro ranks named neighbourhoods on a map and shows its working.",
  skipToContent: "Skip to content",
  navLabel: "Site",
  footerLabel: "About this website",
  nav: {
    home: "Search",
    vibes: "Vibes",
    methods: "Methods",
    /** Short, so that the name of the site and its four links stand on one line of a phone. */
    sources: "Sources",
    accessibility: "Accessibility",
  },
  footer: {
    release: "Data release",
    engine: "Ranking engine",
  },
} as const;

/** The banner that says the data is made up. It is on every page and cannot be closed. */
const MADE_UP = "This is made-up test data.";
const NOT_REAL = "The city, its places and every figure are invented. Nothing here describes a real place.";

export const BANNER = {
  label: "About this data",
  text: `${MADE_UP} ${NOT_REAL}`,
  /**
   * The first sentence, which is all of the banner on a narrow screen once a search is
   * open, so that the answer comes first. Everywhere else the banner says all of it.
   */
  short: MADE_UP,
  rest: NOT_REAL,
} as const;

/**
 * What is shown in place of a page when the service answers with another kind of data
 * than the page was built on: made up where the page is real, or the other way, or a
 * preview where the page is finished, or the other way. Nothing of the page is shown,
 * so that no figure is read under a notice that is not true of it.
 */
export const DISAGREES = {
  heading: "This page cannot be shown",
  text:
    "This page was built on one kind of data, and the service now answers with another: " +
    "one of them is made up or unfinished, and the other is not. Nothing is shown, so that " +
    "no figure is read under the wrong notice. The website must be built again on the " +
    "release the service holds.",
} as const;

/**
 * The banner that says the release is not finished. It is on every page built on a
 * preview and cannot be closed. It says nothing of whether the figures are made up:
 * the banner above does, and a preview of real data does not show that one.
 */
export const PREVIEW_BANNER = {
  label: "About this release",
  text:
    "This is a preview for the people who build Burro. It is not finished: " +
    "what it has not measured is missing, and nothing in it has been approved for the public.",
  /**
   * Said after it on a preview of data that is not made up. Which places the figures are
   * of is the release's to say: the page names them, and this line names none.
   */
  real: "Its figures are of real places, from published data.",
} as const;

/**
 * How Burro itself handles a person's words, as the line under the prompt box says it.
 * It is true whoever else reads them, and it names nobody else: who else reads what is
 * typed, what is sent with it, how long it is kept and where, are the API's to say
 * (`reader`, route 11), and are shown as they are served.
 */
export const WORDS_LINE = "What you type is sent to Burro to be read, and Burro does not keep it.";

/**
 * What stands where the API's notice will stand, until the service has said who reads
 * what is typed. No sentence is sent before it has.
 */
export const READER = {
  label: "Who reads what you type",
  /** The words of the link to the company's own terms. The address is the service's. */
  terms: "Read those terms",
  checking: "Burro is asking the service who else reads what you type. Nothing is sent until it has said.",
  unsaid: "The service has not said who else reads what you type, so nothing you type is sent.",
} as const;

export const NOT_FOUND = {
  title: "Page not found",
  text: "There is no page at this address.",
  back: "Go to the search",
} as const;

export const FAULT = {
  title: "Something went wrong",
  text: "This page could not be shown.",
  retry: "Try again",
} as const;
