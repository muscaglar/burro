/**
 * Site copy for the data sources page. The sources themselves, with their
 * licences and attributions, come from the API, and a credit is shown word for
 * word as its publisher asks for it.
 *
 * It is written for somebody who has never seen Burro: in whole sentences that
 * say what follows from what.
 */

export const SOURCES = {
  title: "Data sources and licences",
  lead: "Every figure Burro shows comes from one of the sources listed here. For each one you can see who published it, the licence it is shared under, a link to the publisher, and the credit that the publisher asks for.",
  /** What is in sight of every source, beside its credit. */
  rows: {
    publisher: "Published by",
    licence: "Licence",
    link: "Publisher's page",
  },
  /** In place of a link, of a source whose publisher gives no page. */
  noLink: "The publisher gives no page for it",
  /**
   * Under a credit that holds a gap the publisher's words leave to be filled, such as the
   * year of the data. Nothing is written into it here: which year it is has a source too.
   */
  unfinished:
    "This credit is not finished yet, because the year of the data still has to be filled in. Burro shows it as the publisher worded it, and has written nothing into the gap.",
  /** What opens the rest of what is said of a source. It is said of which source to whoever hears the page. */
  more: "What Burro uses it for",
  /** In the fold: when Burro took its copy. The date stands between the two, and is the API's. */
  copied: {
    before: "Burro took its copy of this source on",
    after: ".",
  },
  /** Over the measurements that came from a source, by the names the API gives them. */
  usedFor: "Burro works out these measurements from it:",
  notUsed: "Burro does not work out any measurement from this source yet.",
  none: "Burro's data names no source yet, which means there is nothing to list here.",
} as const;
