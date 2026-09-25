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
  MetaData,
  OptionKind,
  RejectReason,
  UnmetCategory,
  UnrankedReason,
} from "@/lib/api/schema";

import { CRIME_RULE, ruleIn } from "./crime";

export const SEARCH = {
  title: "Decide where to live",
  lead: "Describe the life you want and name the places you need to reach. Burro ranks areas and shows its working.",
  /** The same, where the data names no place to reach. */
  leadNoJourneys: "Describe the life you want. Burro ranks areas and shows its working.",
  skipToResults: "Skip to results",
  skipToMap: "Skip to the map",
  skipMap: "Skip the map",
  formLabel: "Your search",
} as const;

/**
 * What the page is for, in a line. It speaks of places to reach only where the data
 * names some.
 */
export function leadFor(holds: Pick<MetaData["holds"], "journeys">): string {
  return holds.journeys ? SEARCH.lead : SEARCH.leadNoJourneys;
}

export const PROMPT = {
  label: "Describe the life you want",
  hint: "Say what you can pay, where you need to get to, and what you want nearby.",
  /**
   * The hint where the data cannot answer all of it. It asks only for what can be
   * answered, and says what cannot: a budget that was asked for and could not be
   * tested once left no area ranked.
   */
  hintFor: (holds: MetaData["holds"]): string =>
    holds.costs && holds.journeys
      ? PROMPT.hint
      : holds.costs
        ? "Say what you can pay and what you want nearby. This data holds no journey times yet."
        : holds.journeys
          ? "Say where you need to get to and what you want nearby. This data holds no rents and no prices yet."
          : "Say what you want nearby. This data holds no rents, no prices and no journey times yet.",
  /** The label once a search is open: what is typed next does not begin a new one. */
  labelOpen: "Add to this search",
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

/** How many examples the page shows. */
export const EXAMPLES_SHOWN = 3;

/**
 * A sentence to start from, and everything it asks for, as the API names each thing in
 * the target of a suggestion. An example is shown only where the data can answer all of
 * it: two of the three that were first written ranked no area on a first build. A test
 * holds what each asks for to what the reader makes of it.
 */
export interface Example {
  readonly text: string;
  readonly asks: readonly string[];
}

/**
 * Sentences to start from, in the order they are tried. The first three that the data
 * can answer are shown. None names a place, so none can go stale.
 */
export const EXAMPLE_POOL: readonly Example[] = [
  {
    text: "Renting a one bedroom flat for about £1,700 a month, somewhere leafy and quiet",
    asks: ["budget", "tag:leafy", "tag:quiet_residential"],
  },
  {
    text: "Buying a terraced house, with good primary schools and a park nearby",
    asks: ["feature:school_primary_attainment", "feature:park_proximity"],
  },
  {
    text: "Somewhere buzzy with bars and restaurants, close to a station",
    asks: ["tag:pace", "feature:venue_evening_per_homes", "feature:venue_food_drink_per_homes", "feature:station_walk"],
  },
  { text: "Somewhere quiet, near a big park", asks: ["tag:quiet_residential", "tag:parks_close_by"] },
  { text: "Clean air and a park nearby", asks: ["feature:air_no2", "feature:park_proximity"] },
  {
    text: "Buying a house, somewhere quiet with clean air",
    asks: ["feature:air_no2", "tag:quiet_residential"],
  },
];

/** The three that were first written, which a release that holds everything shows. */
export const EXAMPLES: readonly string[] = EXAMPLE_POOL.slice(0, EXAMPLES_SHOWN).map((example) => example.text);

/**
 * The shelf of vibes a search can start from. Every word on it, the name of a vibe, what it
 * means, what it is made of and what it cannot see are the API's.
 */
export const SHELF = {
  title: "Start from a word",
  more: "More words",
  fewer: "Fewer words",
  recipe: "What it is made of",
  cannotSee: "What it cannot see",
  scale: (low: string, high: string) => `A scale, from ${low} to ${high}.`,
  share: (hundredths: number) => `${hundredths} of 100:`,
  missing: (count: number) =>
    count === 1 ? "One part of this recipe is not in this data." : `${count} parts of this recipe are not in this data.`,
  /** Over the words that no area can be placed on yet. Each still opens, and says what it waits on. */
  waiting: "Not in this data yet",
  /** In the card of such a word, in place of the button that adds it. The name is the API's. */
  notPlaced: (vibe: string) => `Burro cannot place any area on ${vibe} yet, so it cannot be added to a search.`,
  /** How much of a recipe the data holds, as one number, and how much an area needs. Both are the API's. */
  held: (held: number, needed: number) =>
    held === 0
      ? `This data holds none of its recipe. An area needs ${needed} of 100 to be placed.`
      : held >= needed
        ? `A band rests on ${held} of 100 of its recipe, which is what this data holds.`
        : `This data holds ${held} of 100 of its recipe. An area needs ${needed} of 100 to be placed.`,
  whole: "This data holds the whole of its recipe.",
  /** Over the parts of a recipe that the data does not hold, each by the name the API gives it. */
  waitsOn: "What it waits on",
  notHeld: "Not in this data",
  add: "Add to my search",
  addToward: (end: string) => `Add, towards ${end}`,
  close: "Close",
} as const;

/**
 * What Burro read in a prompt and did not apply. What each offer would do, what follows
 * for areas and the words of each choice are the API's. These are the words of the block
 * that holds them.
 */
export const SUGGEST = {
  title: "Choose what to add",
  /** Under the heading, in one line: that nothing is added until it is pressed. */
  why: "Nothing is added until you press it.",
  /** Beside the way Burro reads the words. It marks a choice, and applies nothing. */
  guess: "Burro's guess",
  /** Before the person's own words, which are cut from the box by where they stand. */
  wrote: "You wrote",
  /** While a model reads what the rules left unread. What the rules noticed is on the page. */
  reading: "Burro is still reading the rest of your words.",
  /** The one button that adds every thing in sight that one press may add. */
  addAll: (count: number) => `Add all ${count}`,
  /** The same, where a thing that is the person's to choose is in sight as well. */
  addThese: (count: number) => `Add the ${count} that need no choice`,
  /**
   * What one press did, in full: how many it added, how many areas a firm budget among them
   * left out, and what is left for the person, which the API names. `leftOut` is `null`
   * where no firm budget was among them, and until the ranking that follows is in.
   */
  added: (
    count: number,
    needs: readonly string[],
    leftOut: number | null = null,
    heldAgainst: string | null = null,
  ) =>
    [
      `${count} added.`,
      leftOut === null ? "" : SUGGEST.leftOut(leftOut, heldAgainst),
      needs.length === 0
        ? ""
        : `${needs.length} ${needs.length === 1 ? "needs" : "need"} you: ${needs.join("; ")}.`,
    ]
      .filter((line) => line !== "")
      .join(" "),
  /**
   * How many areas a firm budget left out, as the API lists them, and where each is listed.
   * `heldAgainst` is what the API says of the rents the budget was held against, where each
   * is of a postcode district or a borough: the line says so, in the API's words.
   */
  leftOut: (count: number, heldAgainst: string | null = null): string => {
    const of = heldAgainst === null ? "" : ` ${heldAgainst}`;
    if (count === 0) return `Your budget is a firm limit. It left no area out.${of}`;
    const [areas, which] = count === 1 ? ["1 area", "it"] : [`${count} areas`, "each"];
    return `Your budget is a firm limit and left out ${areas}: the table of all areas lists ${which}.${of}`;
  },
  takeBack: "Take it all back",
  takenBack: "Taken back. Nothing of it is added.",
  /** A choice that is said of every offer, named by the thing it is a choice of. */
  named: (choice: string, thing: string) => `${choice}: ${thing}`,
  /** Over the field where a place is chosen for a journey whose place Burro does not know. */
  whichPlace: "Which place?",
  /** Over the places the release holds that are like the one that was typed. */
  alike: "Places like it",
  showWords: "Show the words",
  showWordsOf: (thing: string) => `Show the words in the box: ${thing}`,
  showAll: (count: number) => `Show all ${count}`,
  /**
   * The one line that what is left folds to, once one press has added what it may. It says
   * how many are left, under the line that names each, and opens them all.
   */
  showLeft: (count: number) => (count === 1 ? "Show the one left to choose" : `Show the ${count} left to choose`),
  /** Selects, in the box, a part of what was typed that the reader made nothing of. */
  showUnread: "Show in the box",
  showNextUnread: "Show the next in the box",
  /** Beside the button, where a part of what was typed was not read. */
  unread: "Some of your words were not read.",
  wordsShown: "The words are selected in the box.",
} as const;

/**
 * What was asked for that the data does not hold yet. The name of each thing, how much of a
 * recipe is held and the name of each part it waits on are the API's.
 */
export const NOT_IN_DATA = {
  title: "Not in this data yet",
  /** After the title, on its line: each thing by its name. Why is one press away. */
  named: (names: readonly string[]) => `: ${names.join("; ")}`,
  lead: (count: number) =>
    count === 1
      ? "You asked for one thing this data cannot answer yet. It counts for nothing in the ranking."
      : `You asked for ${count} things this data cannot answer yet. They count for nothing in the ranking.`,
  budget: "What you can pay",
  commute: "A journey",
  /** Why, for each kind of thing. */
  why: {
    budget: "This data holds no rents and no prices, so a budget cannot be tested.",
    commute: "This data names no place to reach and holds no journey times.",
    feature: "This data holds no figure for it.",
    vibe: "No area can be placed on it yet.",
  },
  waitsOn: (parts: string) => `It waits on: ${parts}.`,
  part: (label: string, hundredths: number) => `${label}, ${hundredths} of 100`,
  /** The way to what every vibe holds and waits on. */
  more: "What each vibe waits on",
} as const;

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
  /** In place of the name of a place, where an answer named a place and gave no name for it. */
  noName: "A place with no name in this data",
  /** In place of the field, where the data names no place: no spelling could match. */
  notInData:
    "This data names no places yet, so Burro cannot work out a journey. Nothing you type here could match.",
} as const;

/**
 * The same box, where it finds an area by its name too. An area that matches is a link to
 * its page, and is no place to reach: it adds nothing to the search.
 */
export const FIND_AREA = {
  /** The box where the data names places to reach. */
  label: "A place you need to reach, or an area by name",
  hint: "A station, a workplace, a school, a district or a neighbourhood. Type two letters or more.",
  /** The box where the data names no place to reach: an area is all it can find. */
  labelAlone: "Find an area by name",
  hintAlone:
    "The name of a neighbourhood. Type two letters or more. This data names no places to reach yet, so Burro cannot work out a journey.",
  /** Over the areas that match. Each is a link to the page of its area. */
  title: "Areas of that name",
  none: "No place and no area matches. Try another spelling.",
  noneAlone: "No area matches. Try another spelling.",
  found: (places: number, areas: number) =>
    [
      ...(places > 0 ? [places === 1 ? "1 place found" : `${places} places found`] : []),
      ...(areas > 0 ? [areas === 1 ? "1 area found" : `${areas} areas found`] : []),
    ].join(", "),
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
  rankedUnnamed: (count: number) => (count === 1 ? "1 area ranked." : `${count} areas ranked.`),
  /**
   * The first result, named for whoever hears the line and cannot see the card under it.
   * It is not drawn: the first card stands directly under the line and gives the name.
   */
  first: (name: string) => `First: ${name}.`,
  /** The whole of what is said of a first ranking: how many areas, and which is first. */
  ranked: (count: number, first: string): string => `${STATUS.rankedUnnamed(count)} ${STATUS.first(first)}`,
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
  /** Said when the settings nobody chose came to count for less, in the words of a first reader. */
  gaveWay: "What you asked for counts most.",
  /**
   * Said in its place where a journey or a budget counts for more than anything that was
   * asked of the place. A person who asked for leafy and quiet must not read the first
   * result as the leafiest. It is short, so that the line stays one line on a phone.
   */
  leads: (journeys: number, budget: boolean) =>
    journeys === 0
      ? "Budget counts most."
      : `${journeys === 1 ? "Journey" : "Journeys"}${budget ? " and budget count" : journeys === 1 ? " counts" : " count"} most.`,
  /** A change of tenure takes the budget off: a rent is not a price (contract 5.3). */
  budgetWent:
    "Your budget was taken off, because what you can pay in rent is not what you can pay to buy. Say a new one, or set it in the settings.",
  nothingMatches: "No area passes every limit you set.",
  /**
   * Said in its place where no limit left any area out: every area has too little data for
   * what counts. It blamed the person, who had set no limit.
   */
  nothingRanked: "No area could be ranked. This data holds too little of what counts in your search.",
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
  /** In the row, after what was said of a thing: that the parts not shown were filled in. */
  restAssumed: "rest assumed",
  /** The button at the end of the row, which shows the chips that are not in it. */
  rest: (count: number) => `+${count} more`,
  showFewer: "Show fewer",
  assumedHint: "A part marked \"assumed\" is one you did not say. Burro filled it in, and you can change it.",
  remove: "Remove",
  firm: "firm limit",
  flexible: "flexible",
  within: (minutes: number) => `within ${minutes} minutes`,
  more: "more",
  fewer: "fewer",
  /** A scale, and the end of it that is asked for. Both names are the API's. */
  towards: (vibe: string, end: string) => `${vibe}: towards ${end}`,
  /** Asks for the other end of a scale. */
  turn: "Turn",
  turnTo: (vibe: string, end: string) => `Turn ${vibe} towards ${end}`,
  /** The word a vibe was read from, where the word has two meanings. The word is the API's spelling of it. */
  readFrom: (word: string) => `read from \u201c${word}\u201d`,
  hidden: "hidden",
  only: "only",
  off: "does not count",
  usual: (count: number) => (count === 1 ? "Usual settings: 1" : `Usual settings: ${count}`),
  usualHint: "Usual settings are ones nobody chose. They count for less once you ask for something.",
  /** Said with the hints, where a journey or a budget counts for more than what was asked of the place. */
  leadsHint:
    "Here a journey or the budget counts for more than what you asked of the place. To let the place lead, lower how much journeys or the budget count, in Settings.",
  openSettings: "Press it to open the settings.",
  readBy: {
    model: "Read by AI. Check what it understood.",
    // Short, so that it stands on the heading's line on a phone. Methods says how the rules read.
    rule: "Read without AI.",
  } satisfies Record<InterpreterName, string>,
} as const;

export const NOTICE = {
  label: "About your search",
  degraded: "Your words could not be read just now. The settings below do the same job.",
  /** Said when the provider of the language model would not read what was typed. It names nobody. */
  refused: "The language model would not read this. Burro's rules have read it instead.",
  /** A sentence that Burro reads whole, to show what it can read. It names no place. */
  readable: "leafy and quiet, near a park",
  nothingRead:
    "Nothing in that could be read. Burro reads plain English, such as \u201cleafy and quiet, near a park\u201d. Say it another way, or use the settings below.",
  nothingChanged: "That changed nothing. Your search already says it.",
  /** Beside the box, when only a part of what was typed was read. */
  partLabel: "What was not read",
  partUnread:
    "Burro read only part of what you typed, and the ranking leaves the rest out. Say the rest again in shorter sentences, one thing in each, or use the settings.",
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
  health_services: "Burro has no data on health services other than GP surgeries and pharmacies, so that part was left out.",
  driving: "Burro does not work out journeys by car. It covers public transport, cycling and walking.",
  listings: "Burro does not show homes to rent or to buy. It ranks areas.",
  affordability_verdict: "Burro does not say what you can afford. It shows what homes cost in each area.",
  community_amenities:
    "Burro has no data on places of worship, or on shops and venues for one community, so that part was left out.",
  outside_the_city: "Burro covers one city. A place outside it was left out.",
  street_cleanliness: "Burro has no measure of how clean a street is, so that part was left out.",
  upkeep: "Burro has no measure of how well kept a place is, so that part was left out.",
  ratings: "Burro has no ratings or reviews of any place, so that part was left out.",
  prices_and_hours: "Burro has no data on what a place charges or when it opens, so that part was left out.",
  mobile_coverage: "Burro has no data on mobile signal, so that part was left out.",
  change_over_time: "Burro has no measure of how an area is changing, so that part was left out.",
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
  // The one account of when recorded crime counts, as every page says it.
  crime_needs_explicit_request: CRIME_RULE,
  mismatched_choice: "That setting does not take that choice.",
  nothing_to_change: "That changed nothing.",
};

/**
 * Why an edit was not applied, as a page says it of one release. The rule on recorded crime
 * is followed by what is true of the release, where no vibe of it holds recorded crime.
 */
export function whyRefused(reason: RejectReason, meta?: Pick<MetaData, "tags" | "features">): string {
  return reason === "crime_needs_explicit_request" && meta !== undefined ? ruleIn(meta) : REJECTED[reason];
}

export const REJECTED_LABEL = "What was not applied";

/**
 * What an edit that was not applied was about, where that is a part of the search that the
 * API gives no name: a feature, a vibe, a place and an area are named by the API.
 */
export const REJECTED_PART = {
  tenure: "Renting or buying",
  budget: "Budget",
  journeys: "Journeys",
} as const;

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
  commute_likely_beyond:
    "A journey is likely beyond a firm limit. Estimated from distance, not from a timetable.",
};

export const UNRANKED: Readonly<Record<UnrankedReason, string>> = {
  not_rankable: "Not ranked in this data",
  insufficient_data: "Too little data for what counts in your search",
  character_unknown: "Too little is known of the character that counts in your search",
};

/**
 * Under the results: the areas that are not ranked, listed apart from those that are. The
 * name of an area and the name of each thing it lacks are the API's.
 */
export const APART = {
  /** On the button that opens the list. It is what says, before anything is pressed, that there are such areas. */
  title: (count: number) => (count === 1 ? "1 area is not ranked" : `${count} areas are not ranked`),
  label: "Areas that are not ranked",
  lead: "These areas have no fit and no rank. Where a figure is missing, Burro does not fill it in.",
  /** Over the things an area has no figure for. */
  lacks: "No figure in this data for",
} as const;

/** A limit that could not be tested for an area, because the figure is missing. */
export const UNTESTED: Readonly<Record<FilterReason, string>> = {
  excluded: "Whether you hid this area could not be checked.",
  not_selected: "Whether this is one of the areas you chose could not be checked.",
  over_budget: "Your budget is a firm limit, and it could not be tested here: there is no cost figure.",
  commute_cap: "A journey is a firm limit, and it could not be tested here: there is no journey time.",
  commute_likely_beyond:
    "A journey is a firm limit, and it could not be tested here: there is no journey time.",
};

export const NOTHING_MATCHES = {
  title: STATUS.nothingMatches,
  /** The heading where no limit left any area out. */
  noData: "No area could be ranked.",
  lead: "Each area was left out for one of these reasons.",
  /** Over what the areas have no figure for, each by the name the API gives it. */
  lacks: "What has no figure in this data",
  lacking: (name: string, count: number) => `${name}: ${count === 1 ? "1 area" : `${count} areas`}`,
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
  /** The list from the second result on. The first stands before the map, and the rest after it. */
  restLabel: "Areas in order of fit, from the second",
  firstFive: "Reasons are written for the first five results.",
  waiting: "Results will show here.",
  /** Under the first ten: the button that shows the rest of the list. */
  showMore: (count: number) => (count === 1 ? "Show 1 more" : `Show ${count} more`),
  /** Under the whole list, where areas are ranked below the last one listed. Both counts are the API's. */
  listed: (listed: number, ranked: number) =>
    `${listed} of the ${ranked} areas ranked are listed here. The table of all areas holds every one.`,
  /** Opens the full working of a result, in place. */
  showWorking: "Show the working",
  workingOf: (area: string) => `Show the working: ${area}`,
  /** Leads to the areas most like this one, on the area's own page. */
  moreLike: "More like this",
  moreLikeOf: (area: string) => `More like this: ${area}`,
  /** The heading of the reasons after the first, inside the working. */
  moreReasons: "More of why it fits",
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
  openArea: (area: string) => `Open the page for ${area}`,
  hide: (area: string) => `Hide ${area}`,
  showOnMap: (area: string) => `Show ${area} on the map`,
  actions: "Actions",
  foot: { release: "Data release", engine: "Ranking engine" },
} as const;

/**
 * The strip of vibes under a result's name. The name of a vibe and the names of the ends of
 * a scale are the API's. "least" and "most" are the ends of a vibe that runs one way, as the
 * contract names them (section 7.3), and a test holds them to the facts.
 */
export const STRIP = {
  label: (area: string) => `Vibes of ${area}`,
  least: "least",
  most: "most",
  band: (band: number) => `band ${band} of 5`,
  bands: (low: number, high: number) => `varies within this area, from band ${low} to band ${high} of 5`,
  from: (low: string, high: string) => `counted from ${low} to ${high}`,
  /** Said of a mark to a screen reader, in the name of its picture. */
  asked: "asked for",
  askedFor: (end: string) => `asked for: ${end}`,
  /**
   * Said once, where it can be seen, before the marks it is true of: the vibes that were
   * asked for, and then the others the area sits at an end of.
   */
  group: { asked: "Asked for", also: "Also" },
} as const;

export const COMPLETENESS = {
  // Not "what you asked for": the settings nobody chose count too, for less.
  all: "Based on everything that counts in your search",
  some: (present: number, asked: number) =>
    `Based on ${present} of the ${asked} things that count in your search`,
  /** The heading over the API's sentence for each thing the area has no figure for. */
  missingTitle: "What there is no figure for",
  /**
   * On the result, in sight: what the area has no figure for, by the names the chips give.
   * An area with no figure for a thing that was asked for came first once, and the card
   * said only how many things the fit rested on. Such an area now stands below every area
   * that has the figure, and this line is what says which figure it has none for.
   */
  lacks: (names: readonly string[]) => `No figure here for: ${names.join(", ")}. The fit leaves it out.`,
  /** The same, of what the person asked for. It is said with the weight of a trade-off. */
  lacksAsked: (names: readonly string[]) =>
    `No figure here for what you asked for: ${names.join(", ")}. The fit leaves it out.`,
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
   * Where a journey that was estimated stands against the limit a person set: the three
   * bands of the API, each in the words its fact says it in where it stands alone. An
   * estimate is never given in minutes.
   */
  estimated: {
    likely_within: "Likely within your limit",
    borderline: "Borderline for your limit",
    likely_beyond: "Likely beyond your limit",
  },
  /** What stands wherever an estimate is shown: the API's line, word for word. */
  estimatedFrom: "Estimated from distance, not from a timetable.",
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
   * figure for their part of the fit, because no journey has a time in this data. A person
   * who named a workplace must not read the fit as if it had weighed it.
   */
  notCounted: (journeys: number) =>
    journeys === 1
      ? "The journey does not count towards this fit: it has no time in this data."
      : "Journeys do not count towards this fit: none of them has a time in this data.",
  /** Under the journeys, in place of the line that says which of them the fit is worked out from. */
  usesNone: (journeys: number) =>
    journeys === 1
      ? "This journey does not count towards the fit, because it has no time in this data."
      : "None of these journeys counts towards the fit, because none of them has a time in this data.",
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
  // A price that is one number, as a publisher gives it. No range is drawn for it.
  what: "What this is",
  middleOfAll: "The middle price of homes of this kind, of all sizes",
  soldIn: "Homes sold in",
  /** How many sales a price that was counted rests on. The count is the API's. */
  sales: "Sales it rests on",
  pictureOfOne: "The middle price, with your budget marked beside it",
  belowMiddle: "Your budget is below this middle price.",
  aboveMiddle: "Your budget is above this middle price.",
  atMiddle: "Your budget is this middle price.",
  // A rent that is of a wider place than the area. The place, the months and the count are
  // slots of the fact, and no figure is drawn without them.
  figureOf: "A figure of",
  recordedIn: "Rents recorded in",
  rents: "Rents it rests on, to the nearest ten",
  pictureOfRent: "The range of rents of the place, with the middle and your budget marked on it",
  belowMiddleRent: "Your budget is below this middle rent.",
  aboveMiddleRent: "Your budget is above this middle rent.",
  atMiddleRent: "Your budget is this middle rent.",
} as const;

/**
 * The word for how sure a cost is. It is written as the fact's own slot writes it, in small
 * letters, so that a card says it as the page of an area does, which shows the slot.
 */
export const CONFIDENCE: Readonly<Record<Confidence, string>> = {
  high: "high",
  medium: "medium",
  low: "low",
  // Of a price that is one number. A card says what is not known of it, and not this word.
  unstated: "unstated",
};

/** How many pips stand beside the word. The word says it; the pips repeat it. */
export const CONFIDENCE_PIPS: Readonly<Record<Confidence, number>> = { high: 3, medium: 2, low: 1, unstated: 0 };

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
  /**
   * Before the date of a figure. It is said once, after every source, because it is the
   * date of what is said and not of any one source.
   */
  dataFrom: "Data from",
  /** Between a dataset and who published it. */
  by: "published by",
  madeUp: "Made-up data",
} as const;

export const LOCATOR = {
  title: (area: string) => `Where ${area} is among the areas of this data`,
  /** Under the first picture: every area as one shape, with a ring where this one stands. */
  city: "In the whole of this data",
  /** Under the second: the area drawn close, among those around it. */
  close: "Among the areas around it",
} as const;

