/**
 * Site copy for the shell: the words every page carries.
 *
 * Site copy names controls, states and codes. It never holds a number or a
 * proper noun about a place: those come from the API.
 */

export const SITE = {
  name: "Burro",
  /**
   * What a search engine and a shared link show of the website, under its title. It says
   * who Burro is for first, as the heading of the first page does, then what to tell Burro,
   * in the words the founder gave the box, and what Burro does with it.
   */
  description:
    "Whether you are buying, renting or just visiting, Burro helps you find an area to call your own. " +
    "Tell Burro what's important in your space and the places you need to reach, and it will rank the areas " +
    "on a map and show you why.",
  skipToContent: "Skip to content",
  navLabel: "Site",
  footerLabel: "About this website",
  /**
   * The pages about the website, by the names the name board and the foot lead to them by.
   * Each is short, so that the name of the site and its links stand on one line of a phone.
   */
  nav: {
    vibes: "Vibes",
    methods: "Methods",
    sources: "Sources",
  },
  /**
   * Before the two codes at the foot of every page, which say what the page was built on to
   * whoever reports a fault. Each is a version: "release" and "engine" are words of the design.
   */
  footer: {
    release: "Version of the data",
    engine: "Version of the ranking",
  },
  /**
   * The way from the foot of every page to what is said of what a person types: where it
   * goes, and that it is not kept. It is the word a person looks for at the foot of a page.
   * Whoever hears the page hears the heading of what it leads to after it.
   */
  privacy: "Privacy",
  /** The whole name of that link, to whoever hears the page: the word that is seen, and then where it leads. */
  privacyLeadsTo: (word: string, heading: string) => `${word}: ${heading}`,
} as const;

/** The banner that says the data is made up. It is on every page and cannot be closed. */
const MADE_UP = "This is made-up test data.";
const NOT_REAL = "The city, its places and every figure are invented. Nothing here describes a real place.";

export const BANNER = {
  label: "About the data",
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
    "data the service now has.",
} as const;

/**
 * The banner that says the release is not finished. It is on every page built on a
 * preview and cannot be closed. It says nothing of whether the figures are made up:
 * the banner above does, and a preview of real data does not show that one.
 */
export const PREVIEW_BANNER = {
  label: "About this preview",
  text:
    "This is a preview for the people who build Burro. It is not finished: " +
    "what it has not measured is missing, and nothing in it has been approved for the public.",
  /**
   * All of the banner that is drawn on a narrow screen once a search is open: the rest
   * gives way to the answer, as the rest of the other banner does.
   */
  short: "This is a preview.",
  /**
   * Said after it on a preview of data that is not made up. Which places the figures are
   * of is the release's to say: the page names them, and this line names none.
   */
  real: "Its figures are of real places, from published data.",
} as const;

/**
 * How Burro itself handles a person's words, as the page of methods says it.
 * It is true whoever else reads them, and it names nobody else: who else reads what is
 * typed, what is sent with it, how long it is kept and where, are the API's to say
 * (`reader`, route 11), and are shown as they are served.
 */
export const WORDS_LINE = "What you type is sent to Burro to be read, and Burro does not keep it.";

/** What the website itself says beside the service's notice of who reads, on the page of methods. */
export const READER = {
  /** The words of the link to the company's own terms. The address is the service's. */
  terms: "Read those terms",
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
