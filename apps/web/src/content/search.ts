/**
 * Site copy for the search page: the names of its controls, its states and
 * the words for each code the API sends.
 *
 * Nothing here says anything of a place. A sentence about a place is the
 * API's, and is shown as it came. Where a line below has a gap in it, the gap
 * is filled with a name or a figure the API sent.
 *
 * Each table of codes is typed by the generated enum, so a code the contract
 * gains is a type error here until it has a word.
 */

import type {
  Confidence,
  FilterReason,
  InterpreterName,
  OptionKind,
  RejectReason,
  UnmetCategory,
  UnrankedReason,
} from "@/lib/api/schema";

export const SEARCH = {
  title: "Decide where to live",
  lead: "Describe the life you want and name the places you need to reach. Burro ranks areas and shows its working.",
  skipToResults: "Skip to results",
  skipToMap: "Skip to the map",
  formLabel: "Your search",
} as const;

export const PROMPT = {
  label: "Describe the life you want",
  hint: "Say what you can pay, where you need to get to, and what you want nearby.",
  /** Under the label once a search is open: what is typed next does not begin a new one. */
  hintOpen:
    "What you type now is added to the search you have open. To begin a new search, press Start again.",
  submit: "Search",
  reading: "Reading",
  stop: "Stop",
  tryAgain: "Try again",
  startAgain: "Start again",
  left: (count: number) => (count === 1 ? "1 character left" : `${count} characters left`),
  empty: "Type what you are looking for first, or use the settings below.",
  wordsLink: "How your words are handled",
  examplesTitle: "Examples",
  examplesHint: "An example fills the box. Nothing is sent until you press Search.",
} as const;

/** Three sentences to start from. None names a place, so none can go stale. */
export const EXAMPLES: readonly string[] = [
  "Renting a one bedroom flat for up to £1,700 a month, somewhere leafy and quiet",
  "Buying a terraced house, with good primary schools and a park nearby",
  "Somewhere buzzy with bars and restaurants, close to a station",
];

export const TENURE_CHOICE = {
  legend: "Renting or buying",
  rent: "Renting",
  buy: "Buying",
} as const;

export const PLACE = {
  label: "A place you need to reach",
  hint: "A station, a workplace, a school or a district. Type two letters or more.",
  searching: "Searching",
  none: "No place matches. Try another spelling, or a place nearby.",
  found: (count: number) => (count === 1 ? "1 place found" : `${count} places found`),
  failed: "Places could not be searched just now.",
  full: (most: number) =>
    most === 1 ? "You have named 1 place, which is the most." : `You have named ${most} places, which is the most.`,
  options: "Places that match",
  within: "in",
  /** The name of a place the website was never told the name of. */
  unnamed: (position: number) => `Place ${position}`,
  /**
   * Said under the chips while a place is shown by number. `unnamed` is how
   * many are, and `named` how many places the search holds in all. The number
   * is where the data lists the place, so with more than one place it is said
   * not to be the order they were named in.
   */
  unnamedHint: (unnamed: number, named: number) =>
    [
      unnamed === 1
        ? "Burro cannot show the name of one place you named yet, so it is shown by number."
        : `Burro cannot show the names of ${unnamed} places you named yet, so they are shown by number.`,
      ...(named > 1 ? ["The numbers are the order the data lists your places in, not the order you named them in."] : []),
    ].join(" "),
} as const;

export const PLACE_KIND: Readonly<Record<OptionKind, string>> = {
  station: "Station",
  district: "District",
  postcode_district: "Postcode district",
  university: "University",
  hospital: "Hospital",
  school: "School",
  landmark: "Landmark",
  area: "Area",
};

export const STATUS = {
  reading: "Reading your search",
  ranked: (count: number, first: string) =>
    count === 1 ? `1 area ranked: ${first}.` : `${count} areas ranked. First: ${first}.`,
  rankedUnnamed: (count: number) => (count === 1 ? "1 area ranked." : `${count} areas ranked.`),
  rankedNoOrder: (count: number) =>
    count === 1
      ? "1 area passes. Nothing is set to rank it by."
      : `${count} areas pass. Nothing is set to rank them by, so they are in no order.`,
  moved: (count: number) =>
    count === 0
      ? "No area changed place."
      : count === 1
        ? "1 area changed place."
        : `${count} areas changed place.`,
  /** Said in place of `moved` when the ranking holds fewer areas than it did, or more. */
  rankedNow: (count: number, change: number) =>
    `${count === 1 ? "1 area" : `${count} areas`} ranked, ${Math.abs(change)} ${change < 0 ? "fewer" : "more"} than before.`,
  /** After `rankedNow`: how many of the areas ranked both times stand elsewhere than they did. */
  movedOfTheRest: (count: number) =>
    count === 0
      ? "The rest are in the order they were."
      : `${count} of the rest changed place.`,
  gaveWay: "Settings you did not choose now count for less.",
  /** A change of tenure takes the budget off: a rent is not a price (contract 5.3). */
  budgetWent:
    "Your budget was taken off, because what you can pay in rent is not what you can pay to buy. Say a new one, or set it in the settings.",
  nothingMatches: "No area passes every limit you set.",
  question: "Burro has a question about a place.",
} as const;

export const CHIPS = {
  /** The heading of the chips once words have been read into a search. */
  label: "What Burro understood",
  /** The heading before anything has changed the search: nobody said any of it. */
  startLabel: "What a search starts from",
  /** The heading of a search that no words were read into: one made with the settings, or a shared one. */
  setLabel: "What this search holds",
  assumed: "assumed",
  assumedHint: "A part marked \"assumed\" is one you did not say. Burro filled it in, and you can change it.",
  remove: "Remove",
  firm: "firm limit",
  flexible: "flexible",
  within: (minutes: number) => `within ${minutes} minutes`,
  more: "more",
  fewer: "fewer",
  hidden: "hidden",
  only: "only",
  off: "does not count",
  usual: (count: number) => (count === 1 ? "Usual settings: 1" : `Usual settings: ${count}`),
  usualHint: "Usual settings are ones nobody chose. They count for less once you ask for something.",
  openSettings: "Press it to open the settings.",
  readBy: {
    claude: "Read by AI. Check what it understood.",
    rule: "Read without AI, by fixed rules.",
  } satisfies Record<InterpreterName, string>,
} as const;

export const NOTICE = {
  label: "About your search",
  degraded: "Your words could not be read just now. The settings below do the same job.",
  nothingRead: "Nothing in that could be read as a setting. Say it another way, or use the settings below.",
  nothingChanged: "That changed nothing. Your search already says it.",
  /**
   * Under the API's notice, when nothing else in the sentence was read. The notice is the
   * API's and is shown as it came, and it ends by saying that the rest was applied. Where
   * nothing was, the page says so in its own words (docs/design/web.md, section 13).
   */
  nothingElse:
    "Nothing else in that sentence was read, so your search has not changed. Say the rest in a sentence of its own, or use the settings below.",
  /** Beside the box, when only a part of what was typed was read. */
  partLabel: "What was not read",
  partUnread:
    "Burro read only part of what you typed, and the ranking leaves the rest out. Say the rest again in shorter sentences, one thing in each, or use the settings.",
  showPart: "Show the part that was not read",
  showNextPart: "Show the next part that was not read",
  partShown: (at: number, of: number) =>
    of === 1
      ? "The part that was not read is selected in the box."
      : `Part ${at} of the ${of} that were not read is selected in the box.`,
  partNotFound: "Burro cannot show which part it was.",
  offline: "You are offline. Your search is still here.",
  offlineWaiting: "Your last change will be sent when you are back online.",
  notUpdated: "These results were not updated.",
  requestId: "If you report this, quote",
  stale: "Your search names something this data no longer has.",
  takeOut: (what: string) => `Take ${what} out`,
  thePlace: "the place",
  theArea: "the area",
  theSetting: "the setting",
} as const;

/** Words for a call that gave no answer, when the reason is not the API's own. */
export const FAILURE = {
  timeout: "Burro took too long to answer.",
  network: "Burro could not be reached.",
  offline: NOTICE.offline,
  not_configured: "This copy of the website is not connected to Burro's data.",
  unreadable: "Burro sent an answer that could not be read.",
  aborted: "Stopped.",
} as const;

export const UNMET: Readonly<Record<UnmetCategory, string>> = {
  broadband: "Burro has no data on broadband, so that part was left out.",
  flood_risk: "Burro has no data on flood risk, so that part was left out.",
  health_services: "Burro has no data on health services nearby, so that part was left out.",
  driving: "Burro does not work out journeys by car. It covers public transport, cycling and walking.",
  listings: "Burro does not show homes to rent or to buy. It ranks areas.",
  affordability_verdict: "Burro does not say what you can afford. It shows what homes cost in each area.",
  community_amenities:
    "Burro has no data on places of worship, or on shops and venues for one community, so that part was left out.",
  outside_the_city: "Burro covers one city. A place outside it was left out.",
  other: "Part of what you typed could not be read. Say it another way, or use the settings.",
};

export const UNMET_LABEL = "What could not be answered";

export const REJECTED: Readonly<Record<RejectReason, string>> = {
  unknown_place: "That place is not in this data.",
  unknown_area: "That area is not in this data.",
  not_in_release: "This data cannot rank that.",
  too_many_commutes: "No more places can be added. Remove one first.",
  no_such_commute: "That place is not part of your search.",
  out_of_range: "That number is outside what Burro accepts.",
  segment_not_for_tenure: "That kind of home does not go with the choice of renting or buying.",
  direction_not_allowed: "That counts one way only.",
  crime_needs_explicit_request:
    "Recorded crime counts only when you ask for it by name, or switch it on in the settings.",
  mismatched_choice: "That setting does not take that choice.",
  nothing_to_change: "That changed nothing.",
};

export const REJECTED_LABEL = "What was not applied";

export const CLARIFY = {
  question: "Which place did you mean?",
  questionArea: "Which area did you mean?",
  numbered: (at: number, of: number) => `Question ${at} of ${of}.`,
  search: "Or search for the place",
  leaveOut: "Leave it out",
  none: "Burro did not find the place you named. Search for it here.",
} as const;

export const FILTERED: Readonly<Record<FilterReason, string>> = {
  excluded: "Hidden by you",
  not_selected: "Not one of the areas you chose",
  over_budget: "Over your budget, which is a firm limit",
  commute_cap: "A journey is longer than a firm limit",
};

export const UNRANKED: Readonly<Record<UnrankedReason, string>> = {
  not_rankable: "Not ranked in this data",
  insufficient_data: "Too little data for what counts in your search",
};

/** A limit that could not be tested for an area, because the figure is missing. */
export const UNTESTED: Readonly<Record<FilterReason, string>> = {
  excluded: "Whether you hid this area could not be checked.",
  not_selected: "Whether this is one of the areas you chose could not be checked.",
  over_budget: "Your budget is a firm limit, and it could not be tested here: there is no cost figure.",
  commute_cap: "A journey is a firm limit, and it could not be tested here: there is no journey time.",
};

export const NOTHING_MATCHES = {
  title: STATUS.nothingMatches,
  lead: "Each area was left out for one of these reasons.",
  count: (count: number) => (count === 1 ? "1 area" : `${count} areas`),
  loosen: "Make a limit flexible",
  budgetFlexible: "Make the budget flexible",
  journeyFlexible: (place: string) => `Make the journey to ${place} flexible`,
  showHidden: (area: string) => `Show ${area} again`,
  showAll: (area: string) => `Stop showing only ${area}`,
} as const;

export const RESULTS = {
  title: "Results",
  listLabel: "Areas in order of fit",
  firstFive: "Reasons are written for the first five results.",
  /** A link from what Burro understood to the results, which may be some way down the page. */
  goTo: "Go to the results",
  waiting: "Results will show here.",
  working: "Working out the ranking again",
  fit: "Fit",
  fitOf: (score: number) => `${score} of 100`,
  rank: (rank: number) => `Rank ${rank}`,
  whereTitle: "Where it is",
  reasonsTitle: "Why it fits",
  noReasons: "Nothing this area does well enough to give as a reason.",
  tradeOffTitle: "Trade-off",
  noTradeOff: "No trade-off found for this search",
  reasonsFailed: "The reasons could not be loaded.",
  detailsFailed: "The cost and the station could not be loaded.",
  byModel: "Written by AI, checked against the source",
  more: "More about this result",
  openArea: (area: string) => `Open the page for ${area}`,
  hide: (area: string) => `Hide ${area}`,
  showOnMap: (area: string) => `Show ${area} on the map`,
  actions: "Actions",
  foot: { release: "Data release", engine: "Ranking engine" },
} as const;

export const COMPLETENESS = {
  // Not "what you asked for": the settings nobody chose count too, for less.
  all: "Based on everything that counts in your search",
  some: (present: number, asked: number) =>
    `Based on ${present} of the ${asked} things that count in your search`,
  /** The heading over the API's sentence for each thing the area has no figure for. */
  missingTitle: "What there is no figure for",
} as const;

export const JOURNEYS = {
  title: "Journeys",
  columns: {
    place: "To",
    how: "How",
    typical: "Typical",
    missed: "If you just miss one",
    limit: "Your limit",
    /** Over the one cell that stands for both times, where there is no time to give. */
    time: "How long",
  },
  minutes: (minutes: number) => `${minutes} minutes`,
  within: "within",
  over: "over",
  limit: (minutes: number) => `${minutes} minutes`,
  /** Beside a journey given as the trade-off, whose sentence gives the minutes and not the limit. */
  withinLimit: (minutes: number) => `Within your limit of ${minutes} minutes`,
  overLimit: (minutes: number) => `Over your limit of ${minutes} minutes`,
  beyond: (minutes: number) => `More than ${minutes} minutes`,
  missing: "No journey time in this data",
  /**
   * Under two journeys or more: which of them the fit is worked out from. It
   * is the one that does worst against its own limit, which need not be the
   * one that takes the most minutes.
   */
  usesOne: (place: string) =>
    `Of these journeys, only the one to ${place} counts towards the fit: it does worst against the limit you set for it. You can make the average count instead, in Settings.`,
  usesMean: "The average of these journeys counts towards the fit. You can make only the worst one count instead, in Settings.",
  /**
   * Directly under the fit, where the journeys count for nothing in it: the ranking has no
   * figure for their part of the fit, because a journey has no time in this data. A person
   * who named two workplaces must not read the fit as if it had weighed them. `over` is
   * true when a journey that does have a time is over the limit that was set for it.
   */
  notCounted: (journeys: number, over: boolean) =>
    journeys === 1
      ? "The journey does not count towards this fit: it has no time in this data."
      : over
        ? "Journeys do not count towards this fit: at least one of them has no time in this data. One that has a time is over the limit you set."
        : "Journeys do not count towards this fit: at least one of them has no time in this data.",
  /** Under the journeys, in place of the line that says which of them the fit is worked out from. */
  usesNone: (journeys: number) =>
    journeys === 1
      ? "This journey does not count towards the fit, because it has no time in this data."
      : "None of these journeys counts towards the fit, because at least one of them has no time in this data.",
  /** The link under the journeys, to what "typical" and "if you just miss one" mean. */
  timed: "How journeys are timed",
  notGiven: "Not given",
  notApply: "Does not apply",
} as const;

export const COST = {
  title: "Cost",
  none: "No cost figure in this data",
  to: "to",
  middle: "Middle",
  asOf: "As of",
  confidence: "Confidence",
  aMonth: "a month",
  budget: "Your budget",
  picture: "The range of cost, with your budget marked on it",
  below: "Your budget is below this range.",
  above: "Your budget is above this range.",
  inside: "Your budget is inside this range.",
} as const;

/**
 * The word for how sure a cost is. It is written as the fact's own slot writes it, in small
 * letters, so that a card says it as the page of an area does, which shows the slot.
 */
export const CONFIDENCE: Readonly<Record<Confidence, string>> = {
  high: "high",
  medium: "medium",
  low: "low",
};

/** How many pips stand beside the word. The word says it; the pips repeat it. */
export const CONFIDENCE_PIPS: Readonly<Record<Confidence, number>> = { high: 3, medium: 2, low: 1 };

export const BREAKDOWN = {
  title: "How the fit is worked out",
  caption: "Each thing that counts, and what it adds to the fit",
  columns: {
    thing: "What counts",
    weight: "Counts for",
    share: "Share of the fit",
    adds: "Adds",
    says: "What the data says",
  },
  journey: "Journey",
  budget: "Budget",
  /** There is a figure, and the fact that holds it is not in hand to show. */
  has: "Has a figure",
  hasNot: "No figure",
  outOf: (value: number) => `${value} of 100`,
  percent: (value: number) => `${value}%`,
  roundedDown:
    "Every figure here is rounded down, so what the things add can come to a little less than the fit.",
} as const;

export const SOURCE = {
  button: "Source",
  buttonFor: (what: string) => `Source for ${what}`,
  dataFrom: "Data from",
  madeUp: "Made-up data",
} as const;

export const LOCATOR = {
  title: (area: string) => `Where ${area} is among the areas of this data`,
} as const;

export const VIEWS = {
  label: "Show the results as",
  sideLabel: "Show the areas as",
  list: "List",
  map: "Map",
  table: "Table",
  skipMap: "Skip the map",
} as const;
