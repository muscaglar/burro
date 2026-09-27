/**
 * Site copy for a fact laid out in columns: the name of each column.
 *
 * A fact from an area's profile has no sentence of its own, so its slots are
 * laid out under these names. The values are the API's, already formatted,
 * and are shown as they came. A money slot gets its pound sign and nothing
 * else is added.
 */

import type { TemplateId } from "@/lib/api/schema";

export const FACT_COLUMNS = {
  value: "Figure",
  standing: "Where it sits",
  segment: "Kind of home",
  range: "Range",
  median: "Middle",
  asOf: "As of",
  confidence: "Confidence",
  upper: "Upper end of the range",
  // A price that is one number: the middle of what homes of one kind sold for.
  middleOfAll: "Middle price, homes of all sizes",
  soldIn: "Homes sold in",
  // A price counted from sales says how many it rests on. The count is a slot of the fact.
  sales: "Sales it rests on",
  // A rent that is of a wider place than the area: the place it is of, the months the rents
  // were recorded in, and how many they were. Each value is a slot of the fact.
  middleRent: "Middle rent",
  figureOf: "A figure of",
  recordedIn: "Rents recorded in",
  rents: "Rents it rests on, to the nearest ten",
  amount: "Your budget",
  under: "Under your budget by",
  over: "Over your budget by",
  /** Over where a cost stands against the budget, where it is the budget to the pound. The API says where. */
  againstBudget: "Against your budget",
  place: "To",
  mode: "How",
  typical: "Typical minutes",
  missed: "Minutes if you just miss one",
  minutes: "Minutes",
  moreThan: "More than, in minutes",
  name: "Name",
  borough: "Borough",
  station: "Station",
  walk: "Minutes on foot",
  lines: "Lines",
  to: "to",
  limit: "Your limit, in minutes",
  /**
   * Over where a journey stands against the limit, in the API's words: one that was
   * estimated, and one that takes the minutes of its limit.
   */
  estimate: "Against your limit",
  howKnown: "How this is known",
  underLimit: "Under your limit by, in minutes",
  overLimit: "Over your limit by, in minutes",
  band: "Band, of five",
  bands: "Varies within this area, across bands",
  ends: "Counted from",
  compared: "Areas compared in this release",
  partsDated: "Parts dated",
  partsKnown: "Parts with a figure in this release",
  parts: "Parts in the recipe",
  // No figure stands in the name of a column: every figure on a page is a slot of a fact.
  share: "Share of the recipe they carry, in hundredths",
  other: "Alike",
  same: "Measures in the same band",
  measures: "Measures compared",
  leastAlike: "Least alike in",
} as const;

/** Said of an area a vibe cannot place, in place of a band. It names a state and no figure. */
export const CANNOT_PLACE = "Burro cannot place this area on it";

/**
 * Said of a price that is one number, where a range would stand its two ends. It is of the
 * kind of figure and of no place: a publisher's own middle price holds no more than this.
 */
export const ONE_NUMBER = "The publisher gives no range, and does not say how many sales this figure rests on.";

/** What each kind of row is called when nothing else names it. */
export const FACT_KIND: Readonly<Record<TemplateId, string>> = {
  area: "Area",
  feature: "Feature",
  feature_crime: "Recorded crime",
  vibe: "Vibe",
  vibe_range: "Vibe",
  vibe_unknown: "Vibe",
  cost_rent: "Rent",
  cost_buy: "Price",
  cost_buy_median: "Price",
  cost_buy_sold: "Price",
  cost_rent_recorded: "Rent",
  budget_under: "Budget",
  budget_over: "Budget",
  budget_at: "Budget",
  budget_under_median: "Budget",
  budget_over_median: "Budget",
  budget_at_median: "Budget",
  budget_under_recorded: "Budget",
  budget_over_recorded: "Budget",
  budget_at_recorded: "Budget",
  travel_pt: "Journey",
  travel_pt_over: "Journey",
  travel_other: "Journey",
  travel_other_over: "Journey",
  travel_beyond: "Journey",
  travel_estimated: "Journey, estimated",
  station: "Nearest station",
  station_nearby: "Station within a short walk",
  missing: "No figure",
  missing_journey: "No journey time",
  likeness: "Likeness",
  likeness_same: "Likeness",
};
