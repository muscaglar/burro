/**
 * Site copy for an area's page: the names of its headings and its states.
 *
 * Nothing here says anything of a place. Every name and every figure on the
 * page is the API's, and is shown as it came. Where a line below has a gap
 * in it, the gap is filled with a name the API sent.
 */

import type { NameState, Tenure } from "@/lib/api/schema";

/**
 * What is said of the name of an area. The name, the label and who wrote the name are the
 * API's. How far a name has been checked is a code of the API's, and these are its words.
 */
export const NAMED = {
  /** Between the parts of what stands beside a name. */
  between: " \u00b7 ",
  /** Beside a name that no person has checked. */
  draft: "draft name",
  /** On the page of an area, before the label its publisher gives the area. */
  label: "Census area",
  /** On the page of an area, before what is said of its name. */
  name: "Name",
  /** What is said of a name. `by` is who wrote it, as the API names them. */
  state: {
    draft: (by: string) => `A draft, as ${by} writes it. No person has checked it yet.`,
    checked: (by: string) => `As ${by} writes it. A person has checked it.`,
  } satisfies Record<NameState, (by: string) => string>,
  /** The way to the page that says how a name is chosen. */
  how: "How an area is named",
} as const;

export const AREA = {
  /** The title of the page: the area and its borough, as the API names them. */
  title: (area: string, borough: string) => `${area}, ${borough}`,
  /** What the page holds. It describes the page, and says nothing of the place. */
  description: (area: string, borough: string) =>
    `${area}, ${borough}: what it is like, where it is, what homes cost and what is measured there, each figure with its source and date.`,
  borough: "Borough",
  notRanked: "This data does not rank this area, so no search lists it. What is known of it is below.",
  contents: "On this page",
  where: {
    title: "Where it is",
    neighbours: "Areas next to it",
    noNeighbours: "No area in this data is next to it.",
    /** Before the nearest station. Its name, the walk to it and its lines are a fact of the API's. */
    station: "Nearest station",
    /** After the minutes of the walk, which are the fact's own. */
    onFoot: "minutes on foot",
    noStation: "No station near this area is in this data.",
    /** Where the data names no station for any area: it is so of the data, and says nothing of the area. */
    noStations: "This data names no stations yet.",
  },
  /**
   * How long it takes to the places the person named in the search that is open. It is drawn
   * in the browser, from the ranking the search holds: every name and every time is the API's.
   */
  journeys: {
    title: "To the places in your search",
    /** Where the ranking in hand does not hold the area: it is past the results that came, or was left out. */
    notInHand: "Your search names places to reach. The results in hand hold no journey time for this area.",
    toSearch: "Go to the search",
  },
  stations: {
    title: "Stations nearby",
    none: "No station near this area is in this data.",
  },
  cost: {
    title: "What homes cost",
    lead: "Half of homes of this kind cost between these two figures. The middle is the figure half are below.",
    confidence: "What each word for confidence means",
    tenure: { rent: "Renting, a month", buy: "Buying" } satisfies Record<Tenure, string>,
    none: { rent: "No rent figure in this data.", buy: "No price figure in this data." } satisfies Record<
      Tenure,
      string
    >,
  },
  features: {
    title: "What is measured here",
    lead: "Each figure says where it sits among the areas of this data. None is a judgement of the place.",
    noFigure: "No figure in this data",
  },
  /** The areas most like this one. Closed until it is pressed, or come to by a link. */
  alike: {
    open: "More like this",
    title: "Alike in streets, buildings and places",
    /**
     * What the order is, as the contract gives it (section 6.9): the areas in the same band on
     * the most measures come first. The page keeps the order of the answer, and sorts nothing.
     */
    lead: "The areas of this data most like this one, the most alike first: those in the same band as this one on the most measures. Nothing about who lives in a place is compared.",
    none: "This data holds too little about this area to say which areas are like it.",
    /** Before the vibes both areas sit in the same band on. The names are the API's. */
    shares: "On the vibes, both sit in the same band for",
    sharesNone: "On the vibes, the two sit in the same band for none.",
    /** The way to how two areas differ, vibe by vibe. Both names are the API's. */
    compare: (area: string, other: string) => `Compare ${area} with ${other}`,
  },
  sources: {
    title: "Sources on this page",
    lead: "Every figure on this page comes from one of these.",
  },
  compare: "Compare",
  search: "Search for areas",
  methods: "How each figure is worked out",
} as const;

/**
 * The portrait an area's page opens with: where the area sits on each vibe.
 * Every vibe, band, figure and name in it is the API's. These are the
 * headings the API's lists stand under, and the names of what opens.
 */
export const PORTRAIT = {
  title: "Character",
  lead: "Where this area sits on each vibe, in one of five bands among the areas of this data. Press a vibe to see what it is made of.",
  /**
   * What the area is like, in five lines at most: the vibes it sits furthest from the middle
   * on. Every vibe, band and figure in it is the API's. The words for a band are in `bands.ts`.
   */
  short: {
    title: "In short",
    lead: "What sets it apart from the other areas of this data.",
    /** Where no vibe places the area away from the middle, or none places it at all. */
    none: "Nothing sets this area apart on the vibes Burro can place it on.",
    /** Said once where some vibes cannot place the area. Both counts are of the API's lists. */
    unplaced: (count: number, of: number) =>
      count === of
        ? "Burro cannot place this area on any vibe."
        : `Burro cannot place this area on ${count} of the ${of} vibes.`,
    /** The way to why, which is said once, under the vibes. */
    why: "Why not",
    /** What opens the sources and the dates of the lines, which are written out under it. */
    sources: "Sources and dates of these figures",
  },
  /** The heading of each list of the portrait. Which vibe stands in which list is the API's to say. */
  groups: {
    scales: "On a scale",
    more: "More than most here",
    less: "Less than most here",
    others: "Also placed",
    unplaced: "Burro cannot place",
  },
  /** Why a vibe cannot place an area. It is said once, however many vibes it is true of. */
  unplacedWhy:
    "Too few parts of each recipe have a figure for this area, so Burro says nothing of it on these. An area is never put in the middle for want of data.",
  /**
   * Why, of the vibes that no area of the data can be placed on. It is not for want of a
   * figure for this area: the data does not hold enough of the recipe for any.
   */
  notInData:
    "This data does not hold enough of each recipe to place any area on these yet. It is so of every area, and not of this one alone.",
  /** Before the vibes of each kind, where an area has both. */
  ofThisArea: "For want of a figure for this area",
  ofEveryArea: "Not in this data yet",
  /** What opens the parts of each vibe that cannot place the area: one press for all of them. */
  unplacedOpens: "What is known of each",
  /** Between the two counts of a vibe that cannot place the area: the parts with a figure, and the parts of the recipe. */
  of: "of",
  /** At the end of the line of a vibe: what pressing it opens. */
  opens: "Made of",
  madeOf: {
    title: "Made of",
    share: "Share of the recipe",
    /** A share, of the hundred that a recipe adds up to. */
    shareOf: (hundredths: number) => `${hundredths} of 100`,
    reading: "How it is read",
    noFigure: "No figure in this data",
    /** In place of the name of a part that this data does not carry, where the API names none. */
    notCarried: "A part this data does not carry",
    /** Under the name of a part that this data does not carry. Its share is still part of the recipe. */
    waits: "Not in this data yet",
    /** The link to the page that says what every vibe means. It is filled with the vibe's name. */
    about: (vibe: string) => `${vibe}: what it means and what it cannot see`,
  },
  search: {
    button: "Search for this character",
    /** Said beside the button: what pressing it adds. The names are the API's. */
    adds: (vibes: string) => `Adds ${vibes} to your search.`,
  },
} as const;

/**
 * What an area's page ends with: where to start, and what no vibe can say.
 * The station and every line of what a vibe cannot see are the API's.
 *
 * The list is said of the vibes, and never of every figure of the page: a vibe cannot
 * see who lives somewhere, and the same page may offer the census, which says who did.
 */
export const LOOK = {
  title: "Go and look",
  lead: "A figure describes an area, and an area is many streets. Before you decide, walk it.",
  start: "Where to start",
  noStation: "No station near this area is in this data.",
  cannotSee: "What Burro cannot see",
  cannotSeeLead: "No vibe on this page sees any of this. It is for you to see.",
  /** What opens the list of what each vibe cannot see. What none can see is said above it. */
  cannotSeeEach: "What each vibe cannot see",
  vibes: "Every vibe, its recipe and what it cannot see",
} as const;

/** The line that ends a figure on a page that must read with scripts off: its source and its date. */
export const SOURCE_LINE = {
  source: "Source",
} as const;
