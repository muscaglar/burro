/**
 * Site copy for an area's page: the names of its headings and its states.
 *
 * Nothing here says anything of a place. Every name and every figure on the
 * page is the API's, and is shown as it came. Where a line below has a gap
 * in it, the gap is filled with a name the API sent.
 *
 * It is written for somebody who is choosing where to live and has never seen
 * Burro: in whole sentences that are joined, and in no word of the design. A
 * test beside this file holds what each line must still say, however it is put.
 */

import type { NameState, Tenure } from "@/lib/api/schema";

/**
 * What is said of the name of an area. The name, the label and who wrote the name are the
 * API's. How far a name has been checked is a code of the API's, and these are its words.
 */
export const NAMED = {
  /** Between the parts of what stands beside a name. */
  between: " · ",
  /** Beside a name that no person has checked. */
  draft: "draft name",
  /** On the page of an area, before the label its publisher gives the area. */
  label: "Census area",
  /** On the page of an area, before what is said of its name. */
  name: "Name",
  /** What is said of a name. `by` is who wrote it, as the API names them. */
  state: {
    draft: (by: string) =>
      `The name comes from ${by}, and is a draft for this area. No person has checked it yet.`,
    checked: (by: string) => `The name comes from ${by}, and a person has checked it for this area.`,
  } satisfies Record<NameState, (by: string) => string>,
  /** The way to the page that says how a name is chosen. */
  how: "How an area is named",
} as const;

export const AREA = {
  /** The title of the page: the area and its borough, as the API names them. */
  title: (area: string, borough: string) => `${area}, ${borough}`,
  /** What the page holds. It describes the page, and says nothing of the place. */
  description: (area: string, borough: string) =>
    `Read about ${area} in ${borough}: what it is like, where it is, what homes cost and what is measured there, each figure with its source and date.`,
  borough: "Borough",
  notRanked:
    "Burro does not rank this area, which means it will not appear in the results of a search. This page still shows everything Burro knows about it.",
  contents: "On this page",
  where: {
    title: "Where it is",
    neighbours: "Areas next to it",
    noNeighbours: "None of the areas Burro covers is next to this one.",
    noStation: "Burro does not know of a station near this area.",
    /** Where the data names no station for any area: it is so of the data, and says nothing of the area. */
    noStations: "Burro has no information about stations yet, so it cannot say which one is nearest to this area.",
  },
  /**
   * How long it takes to the places the person named in the search that is open. It is drawn
   * in the browser, from the ranking the search holds: every name and every time is the API's.
   */
  journeys: {
    title: "To the places in your search",
    /** Where the ranking in hand does not hold the area: it is past the results that came, or was left out. */
    notInHand:
      "Your search names places you want to reach, but the results Burro has loaded do not include a journey time for this area.",
    toSearch: "Go to the search",
  },
  cost: {
    title: "What homes cost",
    lead: "For each kind of home you will see a range, which is two figures, and a middle. Half of homes of this kind cost between these two figures. The middle is the cost that splits them in two, which means half of these homes cost less than it and half cost more.",
    confidence: "What high, medium and low confidence mean",
    /** Under the rents of an area, where each is of a wider place: it leads to how they are held. */
    rents: "How Burro compares a rent with your budget, and which area each rent covers",
    tenure: { rent: "Rent for a month", buy: "Price to buy", visit: "Price to buy" } satisfies Record<Tenure, string>,
    none: {
      rent: "Burro has no rent figures for this area.",
      buy: "Burro has no sale prices for this area.",
      visit: "Burro has no sale prices for this area.",
    } satisfies Record<Tenure, string>,
  },
  features: {
    title: "What is measured here",
    lead: "This is every measurement Burro has for this area, grouped by subject. Beside each figure you can see how it compares with the same figure for the other areas Burro covers. These are measurements and nothing more, so none of them is a judgement of the area.",
    noFigure: "Burro has no figure for this area.",
  },
  /** The areas most like this one. Closed until it is pressed, or come to by a link. */
  alike: {
    open: "More like this",
    title: "Alike in streets, buildings and places",
    /**
     * What the order is, as the contract gives it (section 6.9): the areas in the same band on
     * the most measures come first. The page keeps the order of the answer, and sorts nothing.
     * The sentence of each area counts "measures compared", in the service's words, so the
     * lead says what a measure is.
     */
    lead: "These are the areas most like this one, the most alike first. To find them, Burro takes each thing it measures about the streets, buildings and places of an area, which it calls a measure, and checks whether the two areas fall in the same band for it. The areas in the same band as this one on the most measures come first. Burro compares nothing about who lives in an area.",
    none: "Burro does not know enough about this area to say which other areas are like it.",
    /** Before the vibes both areas sit in the same band on. The names are the API's. */
    shares: "The two areas are also in the same band for these vibes",
    sharesNone: "The two areas are not in the same band for any vibe.",
    /** The way to how two areas differ, vibe by vibe. Both names are the API's. */
    compare: (area: string, other: string) => `Compare ${area} with ${other}`,
  },
  sources: {
    title: "Sources on this page",
    lead: "Every figure on this page comes from one of the sources listed here. Follow a link to see who publishes a source and the licence it is shared under.",
  },
  compare: "Compare",
  search: "Search for areas",
  methods: "How each figure is worked out",
} as const;

/**
 * What stands at the end of the line of a vibe, and opens what the vibe was worked out from.
 * It was built two ways, for the founder to choose between.
 *
 * `short` is one word, as wide as the "Made of" it takes the place of, so the words that
 * say where the area sits keep their room: on a wide screen the line of a vibe is as high
 * as it was. The sentence over the lists says what a press opens.
 *
 * `full` says by itself what a press opens. It is ten letters wider, and on a wide screen
 * it takes that room from the words beside it: the line of a vibe that sits between two
 * ends was 24 px higher, and its words ran to four lines.
 */
export const OPENS = { short: "Details", full: "What goes into it" } as const;

/** The one line that chooses: `short` or `full`. */
export const OPENS_SAYS: keyof typeof OPENS = "short";

/**
 * The portrait an area's page opens with: where the area sits on each vibe.
 * Every vibe, band, figure and name in it is the API's. These are the
 * headings the API's lists stand under, and the names of what opens.
 */
export const PORTRAIT = {
  title: "Character",
  /** Over the lists of vibes: what a band is, and what pressing a vibe opens. */
  lead: "For each vibe below, Burro compares this area with the others and places it in one of five bands, from the least to the most or from one end to the other. Press a vibe to see the measurements it was worked out from.",
  /**
   * What the area is like, in five lines at most: the vibes it sits furthest from the middle
   * on. Every vibe, band and figure in it is the API's. The words for a band are in `bands.ts`.
   * It is where the portrait first names a vibe, so it says what a vibe is.
   */
  short: {
    title: "In short",
    lead: "A vibe is a way of describing what an area feels like. These are the vibes that most set this area apart from the others.",
    /** Where no vibe places the area away from the middle, or none places it at all. */
    none: "A vibe is a way of describing what an area feels like. On the vibes Burro could work out, it found nothing that sets this area apart from the others.",
    /** Said once where some vibes cannot place the area. Both counts are of the API's lists. */
    unplaced: (count: number, of: number) =>
      count === of
        ? "Burro could not work out any of the vibes for this area."
        : `Burro could not work out ${count} of the ${of} vibes for this area.`,
    /** The way to why, which is said once, under the vibes. */
    why: "Find out why",
    /** What opens the sources and the dates of the lines, which are written out under it. */
    sources: "Sources and dates of these figures",
  },
  /**
   * The heading of each list of the portrait. Which vibe stands in which list is the API's to
   * say (contract, section 7.6): three at most that 60 in 100 of the areas sit below, three at
   * most that as many sit above, and the rest, whatever their band. So the last names no band.
   */
  groups: {
    scales: "Between two ends",
    more: "More of these than most areas",
    less: "Less of these than most areas",
    others: "The other vibes",
    unplaced: "Vibes Burro could not work out",
  },
  /** Why a vibe cannot place an area. It is said once, however many vibes it is true of. */
  unplacedWhy:
    "Burro could not work out these vibes, because too many of the measurements they need are missing for this area. Rather than guess, or put the area in the middle, Burro leaves them blank.",
  /**
   * Why, of the vibes that no area of the data can be placed on. It is not for want of a
   * figure for this area: the data does not hold enough of the recipe for any.
   */
  notInData:
    "Burro cannot work out these vibes for any area yet, because it does not have enough of the measurements they need. This is true of every area, and not only of this one.",
  /** Before the vibes of each kind, where an area has both. */
  ofThisArea: "Because measurements are missing for this area",
  ofEveryArea: "Because Burro does not have the measurements yet",
  /** What opens the parts of each vibe that cannot place the area: one press for all of them. */
  unplacedOpens: "What Burro knows about each of them",
  /** At the end of the line of a vibe: what pressing it opens. `OPENS_SAYS` chooses which. */
  opens: OPENS[OPENS_SAYS],
  madeOf: {
    /**
     * Over the measurements of a vibe. It is not what opened them, whichever of the two the
     * button says: a heading never says its button again. It says what the card of a word,
     * the page of vibes and the settings say, "what goes into it", so that one thing has one
     * name, and says what those things are.
     */
    title: "The measurements that go into it",
    /**
     * How much of the vibe a measurement makes up. It is no "how much it counts": that is
     * where a slider stands, and such figures add up to nothing.
     */
    share: "Its share of the vibe",
    /** A share, of the hundred that a recipe adds up to. */
    shareOf: (hundredths: number) => `${hundredths} of 100`,
    reading: "Which way it counts",
    noFigure: "Burro has no figure for this area.",
    /** In place of the name of a measurement that Burro does not have, where the API names none. */
    notCarried: "A measurement Burro does not have yet",
    /** Under the name of a measurement that Burro does not have. Its share still goes into the vibe. */
    waits: "Burro does not have this measurement yet.",
    /** The link to the page that says what every vibe means. It is filled with the vibe's name. */
    about: (vibe: string) => `More about ${vibe}: what it means and what it cannot see`,
  },
  search: {
    button: "Search for these vibes",
    /** Said beside the button: what pressing it adds. The names are the API's. */
    adds: (vibes: string) =>
      `This adds ${vibes} to your search, so that you can find other areas that have them.`,
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
  lead: "Figures describe an area as a whole, and an area is made up of many streets. That is why it is worth walking around it yourself before you decide.",
  start: "Where to start",
  noStation: "Burro does not know of a station near this area.",
  cannotSee: "What Burro cannot see",
  cannotSeeLead:
    "No vibe on this page can tell you about the things listed here, so they are worth looking out for yourself when you visit.",
  /** What opens the list of what each vibe cannot see. What none can see is said above it. */
  cannotSeeEach: "What each vibe cannot see",
  vibes: "Read about every vibe, and what each one can and cannot tell you",
} as const;

/** The line that ends a figure on a page that must read with scripts off: its source and its date. */
export const SOURCE_LINE = {
  source: "Source",
} as const;
