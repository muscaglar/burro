/**
 * Site copy for the settings: the form that does the same job as the prompt.
 *
 * It names controls. A feature's name and a tag's name are the API's, from
 * the meta route, and are not written here.
 */

import type { Segment, Tenure } from "@/lib/api/schema";

export const SETTINGS = {
  title: "Settings",
  lead: "Every setting here does what typing does. Change one and the ranking is worked out again.",
  rank: "Rank with these settings",
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
} as const;

export const JOURNEY = {
  legend: "Places you need to reach",
  none: "No place named yet.",
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
  // Not "what you want": a feature names a measure, such as noise, which may be wanted low.
  legend: "What counts nearby",
  tagsLegend: "The feel of the place",
  tagsHint: "A tag is a fixed formula over the features above. Methods says what is in each.",
  weight: (label: string) => `How much it counts: ${label}`,
  direction: (label: string) => `Which way counts as better: ${label}`,
} as const;

export const SLIDER = {
  less: (label: string) => `Less: ${label}`,
  more: (label: string) => `More: ${label}`,
  number: (label: string) => `${label}, from 0 to 100`,
  range: "From 0, which is not at all, to 100, which is as much as anything can.",
} as const;

export const HIDDEN = {
  legend: "Hidden areas",
  none: "No area is hidden.",
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
  lead: "Recorded crime is off unless you switch it on. It is a count of what was reported, by kind.",
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
