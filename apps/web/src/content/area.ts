/**
 * Site copy for an area's page: the names of its headings and its states.
 *
 * Nothing here says anything of a place. Every name and every figure on the
 * page is the API's, and is shown as it came. Where a line below has a gap
 * in it, the gap is filled with a name the API sent.
 */

import type { Tenure } from "@/lib/api/schema";

export const AREA = {
  /** The title of the page: the area and its borough, as the API names them. */
  title: (area: string, borough: string) => `${area}, ${borough}`,
  /** What the page holds. It describes the page, and says nothing of the place. */
  description: (area: string, borough: string) =>
    `${area}, ${borough}: what homes cost, the stations nearby and what is measured there, each figure with its source and date.`,
  borough: "Borough",
  notRanked: "This data does not rank this area, so no search lists it. What is known of it is below.",
  contents: "On this page",
  where: {
    title: "Where it is",
    neighbours: "Areas next to it",
    noNeighbours: "No area in this data is next to it.",
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
  tags: {
    title: "The feel of the place",
    lead: "A tag is a fixed formula over the figures above. Methods says what is in each.",
    noFigure: "Not worked out in this data",
  },
  sources: {
    title: "Sources on this page",
    lead: "Every figure on this page comes from one of these.",
  },
  compare: "Compare",
  search: "Search for areas",
  methods: "How each figure is worked out",
} as const;

/** The line that ends a figure on a page that must read with scripts off: its source and its date. */
export const SOURCE_LINE = {
  source: "Source",
} as const;
