/**
 * Site copy for the settings: the form that does the same job as the prompt.
 *
 * It names controls. A feature's name and a tag's name are the API's, from
 * the meta route, and are not written here.
 *
 * It is written for somebody who has never seen Burro: in whole sentences, which say what
 * follows from what. A label is a name, and may be short.
 */

import type { Segment, Tenure } from "@/lib/api/schema";

import { CRIME_RULE } from "./crime";

export const SETTINGS = {
  /**
   * Their name, which is the founder's: over them in Deep search, and under "Refine search".
   * Every line that a visitor reads calls them by it, so that one thing has one name: a
   * line sends a person "under Space requirements", and what they hold is a person's
   * "space requirements". They say nothing of themselves at their head.
   */
  title: "Space requirements",
  /** The button under them, before a search: it names them in short, directly under their name. */
  rank: "Search with these requirements",
  /** The first two groups. The groups after them are named by the API, one for each family of vibes. */
  money: "Budget and home",
  journeys: "Journeys",
  /** Features that belong to no family of vibes and are not recorded crime. */
  airAndNoise: "Air and noise",
} as const;

/**
 * What the bar of a group says of what the group holds, beside its name, so that a person
 * reads what is set without opening anything. It says what a person asked for, in the
 * names the API gives, and nothing of what nobody chose.
 */
export const HOLDS = {
  /** What can be paid. A limit that is not firm is one Burro tries to keep to, and says so. */
  budget: (amount: string, firm: boolean) => (firm ? `up to ${amount}` : `ideally up to ${amount}`),
  /** A place to reach, by the name the API gives it, and the longest journey to it. */
  journey: (place: string, minutes: number, firm: boolean) =>
    firm ? `${place} within ${minutes} minutes` : `${place}, ideally within ${minutes} minutes`,
  /** A scale, and the end of it that is asked for. Both names are the API's. */
  towards: (vibe: string, end: string) => `${vibe} towards ${end}`,
  /** What a person asked to have left out of the ranking. */
  off: (names: string) => `Not counted: ${names}`,
  /** After the first few of a long list. */
  more: (count: number) => `and ${count} more`,
  /** How many are named before the rest are counted. */
  named: 3,
} as const;

/**
 * A search for a home, to rent or to buy: the kinds of search that hold a budget and a kind
 * of home. A visit is the third kind, and holds neither.
 */
export type ForAHome = Exclude<Tenure, "visit">;

/**
 * What a search is for, which the settings ask first: a home to rent, a home to buy, or
 * somewhere to stay on a visit. The third is the founder's, for whoever is looking for
 * where to book a hotel. The words for the first two are older and stand with the words of
 * the search, where the choice reads them, so that each has one name.
 */
export const KIND_OF_SEARCH = {
  /** What is asked, over the three choices. */
  legend: "Renting, buying or visiting",
  visit: "Visiting",
  /**
   * In the place of the budget and the kind of home, which a visit has none of: why they
   * are not asked for, and what the areas are ranked by.
   */
  noBudget:
    "You are visiting, so Burro does not ask what you can pay or what kind of home you want. It ranks the areas " +
    "by everything else you choose, such as the places you need to reach and what you want around you.",
} as const;

export const BUDGET = {
  legend: "Budget",
  amount: {
    rent: "The most you can pay each month, in pounds",
    buy: "The most you can pay, in pounds",
  } satisfies Record<ForAHome, string>,
  less: "Lower the budget a little",
  more: "Raise the budget a little",
  clear: "Clear the budget",
  segment: "Size or type of home",
  firm: "The budget is a firm limit",
  firmHint:
    "With a firm limit, Burro leaves out every area that is known to cost more than your budget. " +
    "Without one, an area that costs more stays in the ranking, but it is ranked lower because of that.",
  weight: "How much the budget counts",
  between: (least: string, most: string) => `Enter an amount between £${least} and £${most}.`,
  notWhole: "Give the amount as a whole number of pounds.",
  /** In place of the amount, where the data holds no cost to test one against. */
  notInData: "Burro has no rents and no prices yet, which means a budget cannot be set.",
} as const;

export const JOURNEY = {
  none: "You have not added a place to reach yet. Use the box above to find one, and Burro will add the journey to your search.",
  /** In place of the field and of every control, where the data names no place to reach. */
  notInData: "Burro has no places to travel to and no journey times yet, which means a journey cannot be added.",
  place: (name: string) => `Journey to ${name}`,
  how: "How you travel there",
  longest: "Longest journey, in minutes",
  shorter: "Make the longest journey shorter",
  longer: "Make the longest journey longer",
  firm: "The journey is a firm limit",
  firmHint:
    "With a firm limit, Burro leaves out every area where the journey is known to take longer. " +
    "Without one, an area with a longer journey stays in the ranking, but it is ranked lower because of that.",
  remove: (name: string) => `Remove ${name}`,
  between: (least: number, most: number) => `Enter a time between ${least} and ${most} minutes.`,
  notWhole: "Give the time as a whole number of minutes.",
  combine: "Which journey counts",
  basis: "Which time counts",
  weight: "How much journeys count",
  settingsLegend: "How journeys count",
} as const;

/** The name of the slider of a thing, and of its two ways, before the name of the thing. */
const HOW_MUCH = "How much it counts";
const WHICH_WAY = "Which way it counts";

export const FEATURES = {
  /**
   * What is seen of the name of the slider of a thing, under the name of the thing: the
   * start of it. The whole of it is what whoever hears the page hears.
   */
  howMuch: HOW_MUCH,
  weight: (label: string) => `${HOW_MUCH}: ${label}`,
  /** The same, of the two ways a measurement can count. */
  whichWay: WHICH_WAY,
  /** Over the two ways a measurement can count. Neither is the better one: a person chooses. */
  direction: (label: string) => `${WHICH_WAY}: ${label}`,
  /**
   * Opens the measurements a vibe is worked out from, each of which can be made to count by
   * itself. It is named as the card of a word, the page of vibes and the page of an area
   * name it, so that one thing has one name.
   */
  madeOf: "What goes into it",
  madeOfName: (vibe: string) => `${vibe}: what goes into it`,
  /** Said under the slider of a vibe, in what goes into the vibe: "this" is what the slider is of. */
  madeOfHint:
    "Burro works this out from the measurements below. You can also make any one of them count in your " +
    "search by itself, by switching it on.",
  /** Measurements of a vibe that Burro does not have, so that none of them can be made to count. */
  notInData: (count: number) =>
    count === 1
      ? "One more measurement goes into it. Burro does not have that one yet, which is why it is not listed here."
      : `${count} more measurements go into it. Burro does not have those yet, which is why they are not listed here.`,
  /** The heading over the measurements of a family that go into no vibe. */
  others: "Other things that count",
} as const;

/**
 * What a switch says of itself, in a word, beside its lamp: whether the thing it is of
 * counts in the search. It is for the eye. Whoever hears the page hears it of the switch.
 */
export const SWITCH = {
  on: "On",
  off: "Off",
} as const;

export const SLIDER = {
  less: (label: string) => `Less: ${label}`,
  more: (label: string) => `More: ${label}`,
  number: (label: string) => `${label}, from 0 to 100`,
  /**
   * What 0 and 100 mean, said once in a group of the settings. It may stand before the first
   * slider of its group, so it names what it speaks of: "The scale" and "it" were of nothing yet.
   */
  range:
    "Each slider here runs from 0 to 100. At 0 the thing does not count at all, and at 100 it counts as much as anything can.",
  /** The button at an end of a slider with two ends. The name of the end is the API's. */
  toward: (label: string, end: string) => `${label}: towards ${end}`,
  /** Where a slider with two ends stands: which end, and how far towards it. */
  towards: (end: string, value: number) => `Towards ${end}, ${value} of 100`,
  /**
   * Where a slider with two ends stands while it is set to neither. What that means is said
   * by the line under it, and is not said here a second time.
   */
  middle: "In the middle",
  twoEnds:
    "While it is in the middle, this does not count at all. The further you move it towards one end, the more " +
    "that end counts, up to 100.",
} as const;

export const HIDDEN = {
  legend: "Hidden areas",
  show: (area: string) => `Show ${area} again`,
  only: (area: string) => `Stop showing only ${area}`,
} as const;

/**
 * The caveat that goes with recorded crime, word for word as the contract
 * states it in section 7.3. A test holds it to the contract.
 */
export const CRIME_CAVEAT =
  "Recorded crime depends on what is reported, and locations are approximate.";

/** What the group of brands holds. It names the group, and says nothing of a place. */
export const BRANDS = {
  lead:
    "The things in this group are about the chains of grocers, gyms and coffee shops that are within reach of home, and " +
    "how far away the nearest of each one is. Burro measures places, not the people in them.",
} as const;

export const CRIME = {
  // The one account of when recorded crime counts, as every page says it.
  lead: `${CRIME_RULE} Each thing here is a count of what was reported, for one kind of crime or incident.`,
} as const;

/**
 * The kinds of home that go with each tenure, in the order a form lists
 * them. The contract names the kinds and the API refuses a kind that does
 * not suit the tenure; no route lists which suit which, so they are held
 * here, and a test holds them to the cost figures the API serves. A visit
 * has no kind of home: the API refuses every kind for one.
 */
export const SEGMENTS: Readonly<Record<Tenure, readonly Segment[]>> = {
  rent: ["room", "studio", "bed_1", "bed_2", "bed_3", "bed_4plus"],
  buy: ["flat", "terraced", "semi_detached", "detached"],
  visit: [],
};
