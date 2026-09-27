/**
 * Site copy for the methods page. It says how Burro works, in words that stay
 * true whatever release is loaded. Every figure about a place, a feature or a
 * limit comes from the API. The few numbers written here are rules of the
 * method that no route serves: how many homes make a cost sure. A test holds
 * each to the project's own record. Who reads what is typed, and what becomes
 * of it there, is the API's to say, and no word of it is written here.
 *
 * It is written for somebody who is choosing where to live and has never seen
 * Burro: in whole sentences that say what follows from what. The page opens
 * with a short account that can be read in a minute. Everything else is one
 * press away, for whoever wants all of it.
 */

import type { HowEstimated } from "@/lib/api/schema";

import { WORDS_LINE } from "./site";
import { TAKEN } from "./taken";

export const METHODS = {
  title: "Methods",
  lead: "This page explains how Burro finds areas for you: what it looks at, how it ranks them, what it will not do, and where its figures come from.",

  /**
   * The short account: four paragraphs, in the order the page promises them. It states no
   * figure, and says nothing of recorded crime in words of its own: the one rule that says
   * when recorded crime counts stands between the two halves of what Burro will not do.
   */
  account: {
    looks:
      "Burro starts from what you tell it: the kind of area you would like, the places you need to reach, and what you can pay. It then compares every area with that, using measurements such as how much green space an area has, how close its shops and stations are, how long your journeys would take and what homes cost.",
    ranks:
      "For each thing you ask for, Burro works out how well every area does, and combines the results into one figure for the area, called the fit. The things you asked for count the most, so the areas at the top of the list are the closest match to them. Because this is plain arithmetic, the same search on the same data always gives the same answer.",
    wont: {
      before:
        "There are things Burro will not do. It does not call any area the best, and it does not guess: when a figure is missing for an area, Burro leaves it out and says so. It ranks places by what is there, and of the people who live in an area it counts only their age and their kind of household, and only when you ask. You cannot ask for fewer of any group of people.",
      after:
        "A language model may help to read what you type, but it never ranks or scores a place, and it never describes one from its own knowledge.",
    },
    sourced:
      "Every figure Burro shows about a place has a source and a date. You can see both by pressing the key beside the figure.",
    /** The two ways on, each a link that stands alone under the paragraph it belongs to. */
    toVibes: "See every vibe, and the key to the drawings",
    toSources: "See who published the data, and under which licence",
  },

  /** What opens all of the rest. It names what it holds, and does not change when it opens. */
  detail: "The methods in full, with every measurement and limit",

  ranking: {
    title: "How the ranking works",
    points: [
      "Burro ranks areas by plain arithmetic over the figures it has. This means the same search on the same data always gives the same ranking.",
      "Each thing you ask for is scored for each area, and the area's fit is the weighted average of those scores, so a thing that counts for more moves the fit more. The things Burro counts in every search still count, but they count for less once you have asked for something.",
      "A firm limit removes an area that is known to break it. A flexible limit keeps the area in the list and lowers its fit instead.",
      "When an area has no figure for something you asked for, that thing is left out for that area and the rest count for more. Nothing is filled in, and the result says how complete it is. Because its fit is then based on less, such an area stands below every area that has the figure, whatever its fit.",
      "An area with a figure for under half of what you asked of the area itself, by how much each thing counts, is not ranked. Journeys and cost do not make up for it, and the area says what it lacks.",
      "Burro ranks places by what is there. Of the people who live in an area it counts two things, and only when you ask: how old they were and what their households were made of, when the census was taken. It counts nothing else about who lives anywhere, and you cannot ask for fewer of anyone.",
      // What Burro does with a sentence, and what it never takes for a person. The second
      // holds the one rule that says when recorded crime counts, word for word.
      TAKEN.does,
      TAKEN.never,
      "A language model may read your words, to work out what you are asking for. It never ranks or scores a place, and never describes one from its own knowledge.",
    ],
  },

  /**
   * How an area comes by its name, as contract 2.2 defines it. It names no place and holds no
   * figure: it is drawn over every city, the made-up one among them. Who wrote a name, and
   * whether a person has checked it, is the API's to say of each area. A test holds these
   * lines to the contract.
   */
  names: {
    title: "How an area is named",
    /**
     * Said first where the data is made up. The names of a made-up city were chosen by no
     * method, and the page of each of its areas leads here all the same.
     */
    madeUp:
      "The names of the areas in this made-up city are invented, as the city is, so none of them was chosen in the way described here. This is how an area of a real city is named.",
    points: [
      "An area is a census area, as the statistics office draws it and labels it: by its borough and a number. Where Burro has the name of a neighbourhood for it, the name comes first and the label stands beside it.",
      "A name is one that a publisher of place names writes for a neighbourhood. Burro coins no name and changes none.",
      "To choose a name, Burro first gives each small census output area to the named neighbourhood nearest to it along the roads. An area then bears the name of the neighbourhood that holds most of its output areas, and an area that no named neighbourhood reaches keeps its label.",
      "A neighbourhood is larger than a census area, so several areas may bear one name. Each says its borough, and where several areas of one borough bear one name, each adds the side it lies on, such as north or south-east.",
      "Every name is a draft until a person has checked it. A draft was chosen by this method alone, which means it may be the name of the neighbourhood next door, or a name few people use. The page of an area says whether its name is a draft, and who wrote it.",
    ],
  },

  features: {
    title: "What is measured",
    lead: "Each measurement describes a place, its buildings, what was recorded there, or who lived there at the census. A measurement about residents says so in its name, and it is about their age or their households and nothing else. For each one you can see how it is worked out, the period it covers and its source, as the data states them.",
    columns: {
      feature: "Measurement",
      definition: "How it is worked out",
      unit: "Unit",
      period: "Period",
      polarity: "Which way it counts",
      sources: "Source",
    },
    notRanked: "Burro shows this measurement, but no search ranks by it yet.",
    /**
     * Of a measure no search ranks on alone, which a vibe's recipe holds all the same. The
     * names of the vibes are the API's.
     */
    partOf: (vibes: string) =>
      `You cannot rank by this measurement alone yet. It still counts, because it is one of the measurements behind ${vibes}.`,
    none: "Burro has no measurement in this group yet.",
  },

  vibes: {
    title: "Vibes",
    lead: "A vibe is a way of describing what an area feels like, and Burro works each one out from a fixed set of the measurements above. A vibe that counts who lived in an area says so, and it counts their age or their households and nothing else. Every area is placed in one of five bands among the areas compared, and is never given a score.",
    link: "Read about every vibe, what goes into it and what it cannot see",
    /** After the link: where what a town is built of is said, now that it is said once. */
    key: "That page begins with a key to every drawing on Burro, which also shows what each little town is built of.",
  },

  defaults: {
    title: "Where a search starts",
    lead: "Before you say anything, a search starts from the things below, which Burro counts in every search. Nobody chose them, which is why they count for less as soon as you ask for something.",
    columns: {
      setting: "What counts",
      value: "Counts for",
      /**
       * Over whether a budget is a firm limit, over which journey counts, and over which way
       * a measurement counts: it is true of all three. The page of vibes heads the same
       * thing of a measurement with the same words.
       */
      direction: "How it counts",
    },
    budget: "Budget",
    journeys: "Journeys",
    home: "Size or type of home",
    weightOf: "of 100",
  },

  /** In place of a setting or a limit of what Burro has no data for. */
  notInData: "Not in Burro's data yet",

  limits: {
    title: "Limits",
    lead: "These are the smallest and the largest values you can set. Nothing outside them can be chosen under Space requirements.",
    /** Said where the data holds no journey, in place of the limits of one. */
    noJourneys: "Burro has no journey times yet, so there is no limit to give for a journey.",
    /** Said where the data holds no rent and no price, in place of the limits of a budget. */
    noCosts: "Burro has no rents and no prices yet, so there is no limit to give for a budget.",
    columns: { limit: "Limit", value: "Value" },
    rows: {
      rent: "Monthly rent",
      buy: "Purchase price",
      minutes: "Longest journey you can set",
      cutoff: "Longest journey Burro has a time for",
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
    notYet: "Burro has no journey times yet. This is how a journey will be timed once it has.",
    points: [
      "A journey is timed door to door, at the weekday morning peak.",
      "By public transport there are two times: the typical one, and the time it takes if you just miss a service. You choose which of the two counts under Space requirements.",
      "By bike and on foot there is one time.",
      "A journey that is longer than the longest Burro has a time for is given as more than that many minutes. The limits above say how many that is.",
      "A short journey counts in full. After that a journey counts for less the longer it is: for a half at the longest time you set, and for nothing at half as long again.",
      "With two places or more, only the journey that does least well against its own limit counts, unless you choose the average under Space requirements.",
    ],
  },

  /**
   * How a journey is estimated, where the data holds no journey time: decision record
   * 0027. It holds no figure of its own. Every number is the API's, from
   * `journey_estimate` of route 11, and the line that stands wherever an estimate is
   * shown is served with them. So what likely within means is said with the number the
   * API serves. What the estimate was held against, and what it could not be held
   * against, is the record's: it was held against timetables on 2026-09-25.
   */
  estimate: {
    title: "How journeys are estimated",
    lead: "Burro has no journey times yet. Until it has, a journey by public transport is estimated from distance, and is said in one of three bands against the limit you set. It is never given in minutes.",
    points: (how: HowEstimated): readonly string[] => [
      `An estimate adds a fixed time to a time for the distance: ${how.fixed_minutes} minutes for the walk to a stop, the wait and the far end, and ${how.minutes_a_km} minutes for each kilometre, in a straight line, between where the homes of an area stand and the place.`,
      `Where the homes of an area are within ${how.near_the_underground_m} metres of an Underground or DLR station, in a straight line, it is ${how.minutes_a_km_near_the_underground} minutes for each kilometre.`,
      `Likely within: the estimate is at least ${how.within_by} minutes under your limit. Likely beyond: it is more than ${how.beyond_by} minutes over it. Anything between the two is borderline. Likely within is what the estimate says, and is no promise.`,
      "A firm limit leaves out only the areas that are likely beyond it. A flexible limit leaves none out: a journey that is likely within it counts in full, one that is borderline counts for a half, and one that is likely beyond it counts for nothing.",
      "An estimate knows nothing of lines, of changes, or of how often anything runs. This means two places the same distance apart are estimated the same, whatever runs between them.",
      "By bike and on foot nothing is estimated.",
      "The estimate has been held against journeys timed from the timetables of the Underground and the DLR. It could not be held against trains, because Burro has no timetable of theirs, so it is less sure for an area whose nearest station is a railway station.",
      "Once Burro has a journey time, the time takes the place of the estimate.",
    ],
  },

  /**
   * How a rent is held, where each rent of the data is of a postcode district or of a
   * borough: decision record 0021, as amended. What is said of the rents themselves is the
   * API's, from `rents` of route 11. It quotes no figure of any place.
   */
  rents: {
    title: "How rents are held",
    points: [
      "No publisher gives a rent for an area as small as one of these. The rents here are the ones recorded over twelve months in each postcode district and each borough, as their publisher gives them: the middle rent, and the two figures that half of the rents lie between.",
      "An area shows the figures of the postcode district where half or more of its homes stand. Where no district holds half, or the district has no such figures, it shows the figures of its borough. Where neither has them it shows none, and nothing is filled in.",
      "Every figure says which place it is of, the months the rents were recorded in, and how many rents it is based on, to the nearest ten. This means two areas of one place show the same figures.",
      "A budget to rent is held against the middle rent of the place. About half of the rents recorded there were under it. As a guide, an area counts in full where the middle rent is within your budget, and for less the further it is over. As a firm limit, an area is left out only where the middle rent is more than a quarter over your budget.",
      "The rents were collected by Rent Officers of the Valuation Office Agency, from the letting agents and landlords who were willing to give them. The figures take no account of how the homes that were let differ in kind or in quality, so they are to be read with caution.",
      "The figures are of rents that were recorded, and not of what is asked for a home today.",
    ],
  },

  /**
   * What each word for how sure a cost is means, as contract 2.5 defines it, and what
   * follows from it for whoever reads the cost: which of them can be trusted the more, in
   * the words of the line over them. No line says that a cost is "less sure": that is what
   * a service said of a vibe, which no page says. The words are the API's codes. A test
   * holds these lines to the contract.
   *
   * The contract says of a range that it is blended or modelled, and no more. A range is
   * blended or modelled where Burro works it out. One that its publisher gives is medium
   * by how many were recorded, and nothing of it is blended: so the line says what is
   * true of both first, and of a range that is blended after it.
   */
  confidence: {
    title: "How sure a cost is",
    /** Said first where the data holds no rent and no price. */
    notYet: "Burro has no rents and no prices yet. This is what each word will mean once it has.",
    lead: "Every range of rents or prices says how far it is to be trusted, in one word. A range is a guide to what homes cost in an area, and says nothing of any one home.",
    rows: {
      high: "High: the range is worked out from at least 50 rents or prices recorded for that kind of home.",
      medium:
        "Medium: only 10 to 49 were recorded, so the range can be trusted less than a high one. A range that Burro works out from so few is blended, which means it is partly an estimate.",
      low: "Low: too few were recorded to work a range out from them, so the range is modelled, which means it is an estimate. It can be trusted the least of the three.",
      unstated:
        "Not stated: the figure is one number, the middle price of the homes of one kind that were sold in a year, as its publisher gives it. The publisher gives no range, and does not say how many sales the figure is based on.",
    },
  },

  /**
   * Which data the page was built on, for whoever reports a fault or sets two answers side
   * by side. It is named as the foot of every page names it: a version, and never a release,
   * which is a word of the design.
   */
  release: {
    title: "This version of the data",
    rows: {
      release: "Version of the data",
      built: "Built",
      engine: "Version of the ranking",
      catalogue: "Version of the list of measurements",
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
      "The website stores nothing in your browser. A search lives in memory, which means it is gone when you close the page.",
      "A shared link holds an id that says nothing about the search. Each place in it is replaced by the station or district that stands in for it, unless you choose to share the exact places.",
      "There is no analytics on this website, and no script, font or image from anyone else.",
    ],
    /**
     * Who else reads what is typed: the API's own words, and its link to the company's terms.
     * The page is built ahead of time, and says so. It points at no line of another page:
     * the one under the search box went when a person who walked the website asked for it to.
     */
    reader: {
      title: "Who else reads what you type",
      asBuilt: "This is what the service said when this page was built.",
    },
  },
} as const;
