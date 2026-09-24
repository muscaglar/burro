/**
 * Site copy for the settings: the form that does the same job as the prompt.
 *
 * It names controls. A feature's name and a tag's name are the API's, from
 * the meta route, and are not written here.
 */

import type { Segment, Tenure } from "@/lib/api/schema";

import { SHELF } from "./search";

import { CRIME_RULE } from "./crime";

export const SETTINGS = {
  title: "Settings",
  lead: "Every setting here does what typing does. Change one and the ranking is worked out again.",
  rank: "Rank with these settings",
  /** The first two groups. The groups after them are named by the API, one for each family of vibes. */
  money: "Budget and home",
  journeys: "Journeys",
  /** Features that belong to no family of vibes and are not recorded crime. */
  airAndNoise: "Air and noise",
} as const;

export const BUDGET = {
  legend: "Budget",
  amount: { rent: "Most you can pay a month, in pounds", buy: "Most you can pay, in pounds" } satisfies Record<
    Tenure,
    string
  >,
  less: "Lower the budget a little",
  more: "Raise the budget a little",
  clear: "Clear the budget",
  segment: "Size or type of home",
  firm: "The budget is a firm limit",
  firmHint: "A firm limit leaves out every area known to cost more. Otherwise a dearer area is ranked lower.",
  weight: "How much the budget counts",
  between: (least: string, most: string) => `Between £${least} and £${most}.`,
  notWhole: "Give the amount as a whole number of pounds.",
  /** In place of the amount, where the data holds no cost to test one against. */
  notInData: "This data holds no rents and no prices yet, so a budget cannot be set.",
} as const;

export const JOURNEY = {
  none: "No place named yet.",
  /** In place of the field and of every control, where the data names no place to reach. */
  notInData: "This data names no places and holds no journey times yet, so a journey cannot be added.",
  place: (name: string) => `Journey to ${name}`,
  how: "How you travel there",
  longest: "Longest journey, in minutes",
  shorter: "Make the longest journey shorter",
  longer: "Make the longest journey longer",
  firm: "The journey is a firm limit",
  firmHint: "A firm limit leaves out every area known to be further. Otherwise a longer journey is ranked lower.",
  remove: (name: string) => `Remove ${name}`,
  between: (least: number, most: number) => `Between ${least} and ${most} minutes.`,
  notWhole: "Give the time as a whole number of minutes.",
  combine: "Which journey counts",
  basis: "Which time counts",
  weight: "How much journeys count",
  settingsLegend: "How journeys count",
} as const;

export const FEATURES = {
  weight: (label: string) => `How much it counts: ${label}`,
  direction: (label: string) => `Which way counts as better: ${label}`,
  /** Opens the parts a vibe is made of, each of which can be made to count by itself. */
  madeOf: "Made of",
  madeOfName: (vibe: string) => `${vibe}: made of`,
  madeOfHint: "A vibe is a fixed recipe over these parts. Each part can also count by itself.",
  /** Parts of a recipe that this data does not carry, so that none of them can be made to count. */
  notInData: SHELF.missing,
  /** The heading over the features of a family that are in no recipe. */
  others: "Other things that count",
} as const;

export const SLIDER = {
  less: (label: string) => `Less: ${label}`,
  more: (label: string) => `More: ${label}`,
  number: (label: string) => `${label}, from 0 to 100`,
  range: "From 0, which is not at all, to 100, which is as much as anything can.",
  /** The button at an end of a slider with two ends. The name of the end is the API's. */
  toward: (label: string, end: string) => `${label}: towards ${end}`,
  /** Where a slider with two ends stands: which end, and how far towards it. */
  towards: (end: string, value: number) => `Towards ${end}, ${value} of 100`,
  middle: "In the middle: it does not count",
  twoEnds: "The middle counts for nothing. The further towards an end, the more that end counts, up to 100.",
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

export const CRIME = {
  // The one account of when recorded crime counts, as every page says it.
  lead: `${CRIME_RULE} It is a count of what was reported, by kind.`,
} as const;

/**
 * The kinds of home that go with each tenure, in the order a form lists
 * them. The contract names the kinds and the API refuses a kind that does
 * not suit the tenure; no route lists which suit which, so they are held
 * here, and a test holds them to the cost figures the API serves.
 */
export const SEGMENTS: Readonly<Record<Tenure, readonly Segment[]>> = {
  rent: ["room", "studio", "bed_1", "bed_2", "bed_3", "bed_4plus"],
  buy: ["flat", "terraced", "semi_detached", "detached"],
};
