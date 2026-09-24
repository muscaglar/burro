/**
 * Site copy for the data sources page. The sources themselves, with their
 * licences and attributions, come from the API.
 */

export const SOURCES = {
  title: "Data sources and licences",
  lead: "Every figure Burro shows comes from one of these sources. Each is listed with its licence and the credit its publisher asks for.",
  rows: {
    publisher: "Publisher",
    licence: "Licence",
    attribution: "Credit",
    retrieved: "Retrieved",
    link: "Publisher's page",
    usedFor: "Used for",
  },
  noLink: "None",
  notUsed: "No feature in this release",
  none: "This release names no source.",
} as const;
