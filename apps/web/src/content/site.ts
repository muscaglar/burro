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
    methods: "Methods",
    sources: "Data sources",
    accessibility: "Accessibility",
  },
  footer: {
    release: "Data release",
    engine: "Ranking engine",
  },
} as const;

/** The banner that says the data is made up. It is on every page and cannot be closed. */
export const BANNER = {
  label: "About this data",
  text:
    "This is made-up test data. The city, its places and every figure are invented. " +
    "Nothing here describes a real place.",
} as const;

/**
 * How a person's words are handled, as the line under the prompt box says it.
 * It promises no more than the project's own record does (ADR 0005), and a
 * test holds it to that.
 */
export const WORDS_LINE =
  "What you type is sent to Burro to be read, and Burro does not keep it. " +
  "If a language model reads it, the model's provider may keep it for up to 30 days, " +
  "or longer if it is flagged.";

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
