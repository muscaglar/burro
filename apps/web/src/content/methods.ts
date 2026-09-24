/**
 * Site copy for the methods page. It says how Burro works, in words that stay
 * true whatever release is loaded. Every figure about a place, a feature or a
 * limit comes from the API. The few numbers written here are rules of the
 * method that no route serves: how long a provider keeps words, and how many
 * homes make a cost sure. A test holds each to the project's own record.
 */

import { WORDS_LINE } from "./site";

export const METHODS = {
  title: "Methods",
  lead: "How Burro ranks areas, what it measures, and where each figure comes from.",

  ranking: {
    title: "How the ranking works",
    points: [
      "Burro ranks areas by arithmetic over published data. The same search on the same data always gives the same ranking.",
      "Each thing you ask for is scored for each area, and the area's fit is the weighted average of those scores. Settings you did not choose count for less once you have asked for something.",
      "A firm limit removes an area that is known to break it. A flexible limit lowers the area's fit instead.",
      "When an area has no figure for something you asked for, that thing is left out for that area and the rest count for more. Nothing is filled in, and the result says how complete it is.",
      "Burro ranks places by what is there. Nothing that describes who lives somewhere is used.",
      "Recorded crime counts only when you ask for it or switch it on.",
      "A language model may read your words into settings. It never ranks or scores a place, and never describes one from its own knowledge.",
    ],
  },

  features: {
    title: "What is measured",
    lead: "Each feature describes a place or its buildings. The definition, the period and the source are as the data release states them.",
    columns: {
      feature: "Feature",
      definition: "How it is worked out",
      unit: "Unit",
      period: "Period",
      polarity: "What counts as better",
      sources: "Source",
    },
    notRanked: "Shown, but not used in ranking in this release.",
    none: "This release carries no feature in this group.",
  },

  tags: {
    title: "Tags",
    lead: "A tag is a fixed formula over the features above. It is named for the place, not for who lives there. The shares of a tag add up to 100.",
    columns: {
      feature: "Feature",
      reading: "How it is read",
      share: "Share of the tag",
    },
    shareOf: "of 100",
  },

  defaults: {
    title: "Where a search starts",
    lead: "Before you say anything, a search starts from these settings. Nobody chose them, so they count for less as soon as you ask for something.",
    columns: {
      setting: "Setting",
      value: "Counts for",
      direction: "Direction",
    },
    budget: "Budget",
    journeys: "Journeys",
    home: "Size or type of home",
    weightOf: "of 100",
  },

  limits: {
    title: "Limits",
    lead: "The form offers no value outside these limits.",
    columns: { limit: "Limit", value: "Value" },
    rows: {
      rent: "Monthly rent",
      buy: "Purchase price",
      minutes: "Longest journey you can set",
      cutoff: "Longest journey in this release",
      places: "Places you can ask to reach in one search",
      text: "Length of a sentence",
      weightStep: "Smallest change to how much something counts",
    },
    to: "to",
    minutes: "minutes",
    characters: "characters",
    inStepsOf: "in steps of",
  },

  /**
   * How a journey is timed and how it counts, as contract 2.6, 6.3 and 6.4
   * define it. It holds no figure: the longest journey a release holds is in
   * the limits, from the API. A test holds these lines to the contract.
   */
  journeys: {
    title: "How journeys are timed",
    points: [
      "A journey is timed door to door, at the weekday morning peak.",
      "By public transport there are two times: the typical one, and the time if you just miss a service. The settings choose which of the two counts.",
      "By bike and on foot there is one time.",
      "A journey longer than this release holds a time for is given as more than that many minutes. The limits above say how many.",
      "A short journey counts in full. After that a journey counts for less the longer it is: for a half at the longest time you set, and for nothing at half as long again.",
      "With two places or more, only the journey that does worst against its own limit counts, unless you choose the average in the settings.",
    ],
  },

  /**
   * What each word for how sure a cost is means, as contract 2.5 defines it.
   * The words are the API's codes. A test holds these lines to the contract.
   */
  confidence: {
    title: "How sure a cost is",
    lead: "Every range of rents or prices says how far it is to be trusted, in one word. A range is a guide to what homes cost in an area, and says nothing of any one home.",
    rows: {
      high: "High: the range is worked out from at least 50 rents or prices recorded for that kind of home.",
      medium: "Medium: from 10 to 49 were recorded, so the range is blended.",
      low: "Low: the range is modelled.",
    },
  },

  release: {
    title: "This data release",
    rows: {
      release: "Release",
      built: "Built",
      engine: "Version of the ranking engine",
      catalogue: "Version of the feature catalogue",
      synthetic: "Made-up data",
      areas: "Areas",
      rankable: "Areas that can be ranked",
      places: "Places you can name",
      stations: "Stations",
      destinations: "Points journeys are measured to",
    },
    yes: "Yes",
    no: "No",
  },

  words: {
    title: "How your words are handled",
    points: [
      WORDS_LINE,
      "What you type travels in the body of a request. It is never put in a web address.",
      "The website stores nothing in your browser. A search lives in memory and is gone when you close the page.",
      "A shared link holds an id that says nothing about the search. Each place in it is replaced by the station or district that stands in for it, unless you choose to share the exact places.",
      "There is no analytics on this website, and no script, font or image from anyone else.",
    ],
  },
} as const;
