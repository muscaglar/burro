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
  amount: "Your budget",
  under: "Under your budget by",
  over: "Over your budget by",
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
} as const;

/** What each kind of row is called when nothing else names it. */
export const FACT_KIND: Readonly<Record<TemplateId, string>> = {
  area: "Area",
  feature: "Feature",
  feature_crime: "Recorded crime",
  tag: "Tag",
  cost_rent: "Rent",
  cost_buy: "Price",
  budget_under: "Budget",
  budget_over: "Budget",
  travel_pt: "Journey",
  travel_other: "Journey",
  travel_beyond: "Journey",
  station: "Nearest station",
  station_nearby: "Station within a short walk",
  missing: "No figure",
};
