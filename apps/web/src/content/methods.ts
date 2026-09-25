/**
 * Site copy for the methods page. It says how Burro works, in words that stay
 * true whatever release is loaded. Every figure about a place, a feature or a
 * limit comes from the API. The few numbers written here are rules of the
 * method that no route serves: how many homes make a cost sure. A test holds
 * each to the project's own record. Who reads what is typed, and what becomes
 * of it there, is the API's to say, and no word of it is written here.
 */

import type { HowEstimated } from "@/lib/api/schema";

import { CRIME_RULE } from "./crime";
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
      "When an area has no figure for something you asked for, that thing is left out for that area and the rest count for more. Nothing is filled in, and the result says how complete it is. Such an area stands below every area that has the figure, whatever its fit.",
      "An area with a figure for under half of what you asked of the place itself, by how much each thing counts, is not ranked. Journeys and cost do not make up for it. The area says what it lacks.",
      "Burro ranks places by what is there. Of the people who live in an area it counts two things, and only when you ask: how old they were and what their households were made of, when the census was taken. It counts nothing else about who lives anywhere, and you cannot ask for fewer of anyone.",
      CRIME_RULE,
      "When your words are not a plain list of what you want, Burro applies none of them. It shows what it noticed, and you choose what to add.",
      "A language model may read your words into settings. It never ranks or scores a place, and never describes one from its own knowledge.",
    ],
  },

  /**
   * How an area comes by its name, as contract 2.2 defines it. It names no place and holds no
   * figure. Who wrote a name, and whether a person has checked it, is the API's to say of
   * each area. A test holds these lines to the contract.
   */
  names: {
    title: "How an area is named",
    points: [
      "An area is a census area, as the statistics office draws it and labels it: by its borough and a number. Where the data holds the name of a neighbourhood for it, the name comes first and the label stands beside it.",
      "A name is one that a publisher of place names writes for a neighbourhood. Burro coins no name and changes none.",
      "Burro's draft of London's neighbourhoods gives each small census output area to the named neighbourhood nearest to it along the roads. An area bears the name of the neighbourhood that holds most of its output areas. An area that no named neighbourhood reaches keeps its label.",
      "A neighbourhood is larger than a census area, so several areas may bear one name. Each says its borough. Where several areas of one borough bear one name, each adds the side it lies on, such as north or south-east.",
      "Every name is a draft until a person has checked it. A draft was chosen by this method alone, so it may be the name of the neighbourhood next door, or a name few people use. The page of an area says whether its name is a draft, and who wrote it.",
    ],
  },

  features: {
    title: "What is measured",
    lead: "Each feature describes a place, its buildings, what was recorded there, or who lived there at the census. A feature about residents says so in its name, and is of their age or their households and nothing else. The definition, the period and the source are as the data release states them.",
    columns: {
      feature: "Feature",
      definition: "How it is worked out",
      unit: "Unit",
      period: "Period",
      polarity: "What counts as better",
      sources: "Source",
    },
    notRanked: "Shown, but not used in ranking in this release.",
    /**
     * Of a measure no search ranks on alone, which a vibe's recipe holds all the same. The
     * names of the vibes are the API's.
     */
    partOf: (vibes: string) =>
      `No search ranks on it alone in this release. It counts as a part of ${vibes}.`,
    none: "This release carries no feature in this group.",
  },

  vibes: {
    title: "Vibes",
    lead: "A vibe is a fixed recipe over the features above. A vibe that counts who lived in an area says so, and counts their age or their households and nothing else. An area is placed in one of five bands among the areas compared, and never given a score.",
    link: "Every vibe, its recipe, its sources and what it cannot see",
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

  /** In place of a setting or a limit of what the data does not hold. */
  notInData: "Not in this data yet",

  limits: {
    title: "Limits",
    lead: "The form offers no value outside these limits.",
    /** Said where the data holds no journey, in place of the limits of one. */
    noJourneys: "This data holds no journey times yet, so it has no limit for a journey.",
    /** Said where the data holds no rent and no price, in place of the limits of a budget. */
    noCosts: "This data holds no rents and no prices yet, so it has no limit for a budget.",
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
    /** Said first where the data holds no journey: what follows is what is to come. */
    notYet: "This data holds no journey times yet. This is how a journey is timed once it does.",
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
   * How a journey is estimated, where the data holds no journey time: decision record
   * 0027. It holds no figure of its own. Every number is the API's, from
   * `journey_estimate` of route 11, and the line that stands wherever an estimate is
   * shown is served with them.
   */
  estimate: {
    title: "How journeys are estimated",
    lead: "This data holds no journey times yet. Until it does, a journey by public transport is estimated from distance, and is said in one of three bands against the limit you set. It is never given in minutes.",
    points: (how: HowEstimated): readonly string[] => [
      `An estimate is a fixed part and a part for distance: ${how.fixed_minutes} minutes for the walk to a stop, the wait and the far end, and ${how.minutes_a_km} minutes for each kilometre, in a straight line, between where the homes of an area stand and the place.`,
      `Where the homes of an area are within ${how.near_the_underground_m} metres of an Underground or DLR station, in a straight line, it is ${how.minutes_a_km_near_the_underground} minutes for each kilometre.`,
      `Likely within: the estimate is at least ${how.within_by} minutes under your limit. Likely beyond: it is more than ${how.beyond_by} minutes over it. Anything between the two is borderline.`,
      "A firm limit leaves out only the areas that are likely beyond it. A flexible limit leaves none out: a journey that is likely within it counts in full, one that is borderline counts for a half, and one that is likely beyond it counts for nothing.",
      "An estimate knows nothing of lines, of changes, or of how often anything runs. Two places the same distance apart are estimated the same, whatever runs between them.",
      "By bike and on foot nothing is estimated.",
      "The numbers are a first guess. They have not been checked against journeys that were timed.",
      "Once the data holds a journey time, the time takes the place of the estimate.",
    ],
  },

  /**
   * What each word for how sure a cost is means, as contract 2.5 defines it.
   * The words are the API's codes. A test holds these lines to the contract.
   */
  confidence: {
    title: "How sure a cost is",
    /** Said first where the data holds no rent and no price. */
    notYet: "This data holds no rents and no prices yet. This is what each word means once it does.",
    lead: "Every range of rents or prices says how far it is to be trusted, in one word. A range is a guide to what homes cost in an area, and says nothing of any one home.",
    rows: {
      high: "High: the range is worked out from at least 50 rents or prices recorded for that kind of home.",
      medium: "Medium: from 10 to 49 were recorded, so the range is blended.",
      low: "Low: the range is modelled.",
      unstated:
        "Not stated: the figure is one number, the middle price of the homes of one kind that were sold in a year, as its publisher gives it. The publisher gives no range, and does not say how many sales the figure rests on.",
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
      preview: "A preview that is not finished",
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
    /** What the service says of who else reads what is typed is drawn after the first of these. */
    points: [
      WORDS_LINE,
      "What you type travels in the body of a request. It is never put in a web address.",
      "The website stores nothing in your browser. A search lives in memory and is gone when you close the page.",
      "A shared link holds an id that says nothing about the search. Each place in it is replaced by the station or district that stands in for it, unless you choose to share the exact places.",
      "There is no analytics on this website, and no script, font or image from anyone else.",
    ],
    /** Who else reads what is typed: the API's own words, and its link to the company's terms. */
    reader: {
      title: "Who else reads what you type",
      asBuilt:
        "This is what the service said when this page was built. The line under the search box asks the service again each time the page is opened.",
    },
  },
} as const;
