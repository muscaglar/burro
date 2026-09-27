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
  MetaData,
  OptionKind,
  RejectReason,
  UnmetCategory,
  UnrankedReason,
} from "@/lib/api/schema";

import { CRIME_RULE, ruleIn } from "./crime";
import { JOURNEY, KIND_OF_SEARCH } from "./settings";
import { REFINE } from "./ways";

/** A list of names as a person says one: "Leafy", "Leafy and Quiet streets", "Leafy, Quiet streets and Budget". */
const NAMES = new Intl.ListFormat("en-GB", { style: "long", type: "conjunction" });

/**
 * The same, each in quotation marks, as the page sets the name of a button in a sentence.
 * The name of a thing that counts may be a wish, as "Less transport noise" is: read as
 * words of the sentence, Burro had no figure for less of it.
 */
const named = (names: readonly string[]) => NAMES.format(names.map((name) => `"${name}"`));

/**
 * Who Burro is for, which the page says first and the title of the website says after it:
 * a person who is buying, renting or just visiting, and wants an area of their own.
 */
const FOR_WHOM = "Whether you are buying, renting or just visiting, Burro helps you find an area to call your own.";

export const SEARCH = {
  title: "Find your area",
  /** Who it is for, in the founder's words. It is what a search engine shows of the website too. */
  forWhom: FOR_WHOM,
  /**
   * After it: what to tell Burro, in the words the founder gave the box, and what Burro
   * does with it. The box says "tell me", since Burro speaks there. Here he is spoken of.
   */
  lead:
    `${FOR_WHOM} Tell Burro what's important in your space and the places you need to reach, ` +
    "and it will rank the areas by how well they match and show you why.",
  /** The same, where the data names no place to reach. */
  leadNoJourneys:
    `${FOR_WHOM} Tell Burro what's important in your space, ` +
    "and it will rank the areas by how well they match and show you why.",
  skipToResults: "Skip to results",
  skipToMap: "Skip to the map",
  skipMap: "Skip the map",
  /**
   * What the link that skips the map leads to, said to whoever hears the page as the focus
   * lands there. It is not drawn: a person who sees the page sees where the map ends.
   */
  pastMap: "End of the map",
  formLabel: "Your search",
} as const;

/**
 * What the page is for, in a line. It speaks of places to reach only where the data
 * names some.
 */
export function leadFor(holds: Pick<MetaData["holds"], "journeys">): string {
  return holds.journeys ? SEARCH.lead : SEARCH.leadNoJourneys;
}

/** Said after what helps most, whatever the data holds: why it is worth saying more. */
const THE_MORE_YOU_SAY = "The more you say, the closer the match will be.";

export const PROMPT = {
  /** The heading of the first way in, which is the label of the box. It is the founder's own. */
  label: "Tell me what's important in your space",
  /**
   * Under it: what a useful sentence holds, to whoever has not written one. What can be
   * spent, where to get to and how long that may take, and what is wanted nearby, and that
   * saying more makes a closer match.
   */
  hint:
    "It helps most to say what you can spend, where you need to get to and how long that journey may take, " +
    `and what you want around you. ${THE_MORE_YOU_SAY}`,
  /**
   * The same where the data cannot answer all of it. It asks only for what can be
   * answered, and says what cannot: a budget that was asked for and could not be
   * tested once left no area ranked.
   */
  hintFor: (holds: MetaData["holds"]): string =>
    holds.costs && holds.journeys
      ? PROMPT.hint
      : holds.costs
        ? `It helps most to say what you can spend and what you want around you. ${THE_MORE_YOU_SAY} ` +
          "Burro has no journey times for these areas yet, so it cannot take a journey into account."
        : holds.journeys
          ? "It helps most to say where you need to get to and how long that journey may take, " +
            `and what you want around you. ${THE_MORE_YOU_SAY} ` +
            "Burro has no rents or prices for these areas yet, so it cannot take a budget into account."
          : `It helps most to say what you want around you. ${THE_MORE_YOU_SAY} ` +
            "Burro has no rents, no prices and no journey times for these areas yet, so it cannot take a budget or a journey into account.",
  /**
   * Before one whole sentence as an example, which follows it in marks of its own. The
   * sentence is the first that the data can answer the whole of, and is never written here.
   */
  forExample: "For example, you could write:",
  /** The label once a search is open: what is typed next does not begin a new one. */
  labelOpen: "Add to this search",
  submit: "Search",
  reading: "Reading",
  stop: "Stop",
  tryAgain: "Try again",
  startAgain: "Start again",
  left: (count: number) => (count === 1 ? "1 character left" : `${count} characters left`),
  /**
   * Under the box, where what was pasted has filled it. A browser cuts what is pasted at
   * what the box takes and says nothing of it, and the website does not read what was
   * pasted: so it says that the end may have been left out, and never that it was.
   */
  full: (most: number) =>
    `Burro reads ${most} characters at a time, and the box is now full. If what you pasted was longer than that, ` +
    "the end of it was left out, so please check how your description ends.",
  /** Search was pressed on a box that holds nothing, before a search. The other way in is named. */
  empty:
    "There is nothing in the box to search for yet. Type a description of what you are looking for, " +
    "or use Deep search to choose it without typing.",
  /** The same once a search is open, where the settings stand under the part that refines it. */
  emptyOpen:
    "There is nothing in the box to add yet. Type what you would like to add to your search, " +
    `or change your space requirements under ${REFINE.label}.`,
  examplesTitle: "Examples",
  examplesHint:
    "Choose an example and Burro will put it in the box for you. " +
    "Nothing is sent until you press Search, so you can change the words first.",
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
  /**
   * What a word of the shelf is, and what a press on one does, to whoever has not seen
   * one. It names no vibe: the words of the shelf are the API's.
   */
  lead:
    "Each of these words is a vibe, which is a way of describing what an area feels like. " +
    "Choose one to see what it means and where it is found, and add it to your search if it is what you are looking for.",
  more: "More words",
  fewer: "Fewer words",
  recipe: "What goes into it",
  cannotSee: "What it cannot see",
  scale: (low: string, high: string) => `This is a scale that runs from ${low} to ${high}.`,
  /** Before the name of a measurement: how much of the vibe it makes up. It says what the figure is a figure of. */
  share: (hundredths: number) => `Counts for ${hundredths} of 100:`,
  missing: (count: number) =>
    count === 1
      ? "One of the measurements that go into it is missing from Burro's data."
      : `${count} of the measurements that go into it are missing from Burro's data.`,
  /** Over the words that no area can be placed on yet. Each still opens, and says what it waits on. */
  waiting: "Not available yet",
  /** In the card of such a word, in place of the button that adds it. The name is the API's. */
  notPlaced: (vibe: string) =>
    `Burro cannot work out ${vibe} for any area yet, because too many of the measurements it needs are missing. ` +
    "This means you cannot add it to a search for now.",
  /**
   * How much of what goes into a vibe Burro has, as one number, and how much an area needs.
   * Both are the API's. Each measurement counts for so many of 100 in its vibe, as the list
   * under "What goes into it" says of each, and these are the same hundred.
   */
  held: (held: number, needed: number) =>
    held === 0
      ? `Burro has none of the measurements that go into it yet. It needs measurements that count for ${needed} of 100 in it before it can describe an area with it.`
      : held >= needed
        ? `Burro does not have every measurement that goes into it yet. It works this out from the ones it has, which count for ${held} of 100 in it.`
        : `The measurements Burro has so far count for ${held} of 100 in it, and it needs ${needed} of 100 before it can describe an area with it.`,
  whole: "Burro has every measurement that goes into it.",
  /** Over the measurements of a vibe that Burro does not have, each by the name the API gives it. */
  waitsOn: "What is still missing",
  notHeld: "Missing so far",
  add: "Add to my search",
  addToward: (end: string) => `Add, towards ${end}`,
  close: "Close",
} as const;

/**
 * What the page says of words that Burro did not read, and of words that it reads still.
 *
 * Burro asks nothing: what it noticed in a sentence it takes of itself, and what it took
 * is a chip of what it understood. So nothing here offers a thing to be pressed.
 */
export const SUGGEST = {
  /** While a model reads what the rules left unread. What the rules read is on the page, and ranked. */
  reading: "Burro is still reading the rest of your words.",
  /** Selects, in the box, a part of what was typed that the reader made nothing of. */
  showUnread: "Show in the box",
  showNextUnread: "Show the next in the box",
  /**
   * Beside the button that shows them, wherever words were not read. It is drawn where some
   * of the words were not read and where none of them was, so it does not say how many:
   * "Some of your words were not read" stood under "Nothing in that could be read".
   */
  unread: "Burro can show you the words it did not read.",
} as const;

/**
 * What was asked for that the data does not hold yet. The name of each thing, how much of a
 * recipe is held and the name of each part it waits on are the API's.
 */
export const NOT_IN_DATA = {
  title: "Not in Burro's data yet",
  /** After the title, on its line: each thing by its name. Why is one press away. */
  named: (names: readonly string[]) => `: ${names.join("; ")}`,
  lead: (count: number) =>
    count === 1
      ? "You asked for one thing that Burro has no data for yet. This means it could not be counted, so it makes no difference to the ranking."
      : `You asked for ${count} things that Burro has no data for yet. This means they could not be counted, so they make no difference to the ranking.`,
  budget: "What you can pay",
  commute: "A journey",
  /** Why, for each kind of thing. */
  why: {
    budget: "Burro has no rents and no prices yet, which means it cannot check an area against a budget.",
    commute: "Burro has no places to travel to and no journey times yet, so it cannot work out a journey.",
    feature: "Burro has no figure for it yet.",
    vibe: "Burro cannot work it out for any area yet, because too many of the measurements it needs are missing.",
  },
  waitsOn: (parts: string) => `The measurements it is waiting for are: ${parts}.`,
  /** One measurement a vibe waits for, and how much of the vibe it makes up. */
  part: (label: string, hundredths: number) => `${label}, which counts for ${hundredths} of 100 in it`,
  /** The way to what every vibe holds and waits on. */
  more: "See what goes into each vibe",
} as const;

export const TENURE_CHOICE = {
  /**
   * What is asked over the choice. A visit is the third kind of search, so the settings
   * name all three, and this is their name for it: whatever finds the choice by this finds
   * what the page draws.
   */
  legend: KIND_OF_SEARCH.legend,
  rent: "Renting",
  buy: "Buying",
} as const;

export const PLACE = {
  label: "A place you need to reach",
  hint: "Type the name of a station, a workplace, a school or a district. Burro starts looking once you have typed two letters.",
  searching: "Searching",
  none: "Burro found no place with that name. You could try another spelling, or a place nearby.",
  found: (count: number) => (count === 1 ? "1 place found" : `${count} places found`),
  failed: "Burro could not search for places just now. Please try again in a moment.",
  full: (most: number) =>
    most === 1 ? "You have named 1 place, which is the most." : `You have named ${most} places, which is the most.`,
  options: "Places that match",
  within: "in",
  /** In place of the name of a place, where an answer named a place and gave no name for it. */
  noName: "A place Burro has no name for",
  /** In place of the field, where the data names no place: no spelling could match. */
  notInData:
    "Burro has no places to travel to in its data yet, so it cannot work out a journey. This means nothing you type here could find a match.",
} as const;

/**
 * The same box, where it finds an area by its name too. An area that matches is a link to
 * its page, and is no place to reach: it adds nothing to the search.
 */
export const FIND_AREA = {
  /** The box where the data names places to reach. */
  label: "A place you need to reach, or an area by name",
  hint: "Type the name of a station, a workplace, a school, a district or an area. Burro starts looking once you have typed two letters.",
  /** The box where the data names no place to reach: an area is all it can find. */
  labelAlone: "Find an area by name",
  hintAlone:
    "Type the name of an area, and Burro starts looking once you have typed two letters. Burro has no places to travel to in its data yet, so it cannot work out a journey.",
  /** Over the areas that match. Each is a link to the page of its area. */
  title: "Areas with that name",
  none: "Burro found no place and no area with that name. You could try another spelling.",
  noneAlone: "Burro found no area with that name. You could try another spelling.",
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
  rankedUnnamed: (count: number) =>
    count === 1 ? "Burro has ranked 1 area for you." : `Burro has ranked ${count} areas for you.`,
  /**
   * The first result, named for whoever hears the line and cannot see the card under it.
   * It is not drawn: the first card stands directly under the line and gives the name.
   */
  first: (name: string) => `The first is ${name}.`,
  /** The whole of what is said of a first ranking: how many areas, and which is first. */
  ranked: (count: number, first: string): string => `${STATUS.rankedUnnamed(count)} ${STATUS.first(first)}`,
  rankedNoOrder: (count: number) =>
    count === 1
      ? "1 area passes, but your search holds nothing to rank it by yet."
      : `${count} areas pass, but your search holds nothing to rank them by yet, so they are in no particular order.`,
  moved: (count: number) =>
    count === 0
      ? "No area changed place."
      : count === 1
        ? "1 area changed place."
        : `${count} areas changed place.`,
  /** Said in place of `moved` when the ranking holds fewer areas than it did, or more. */
  rankedNow: (count: number, change: number) =>
    `${count === 1 ? "1 area is" : `${count} areas are`} ranked now, which is ${Math.abs(change)} ${change < 0 ? "fewer" : "more"} than before.`,
  /** After `rankedNow`: how many of the areas ranked both times stand elsewhere than they did. */
  movedOfTheRest: (count: number) =>
    count === 0
      ? "The rest are in the order they were."
      : `${count} of the rest changed place.`,
  /**
   * Said when the settings nobody chose came to count for less: what that means for whoever
   * reads the list. What was asked for counts the most, so the area that matches it most
   * closely stands first. With the line before it, it is two lines on a phone and no more:
   * measured at 390 wide, a third line puts the foot of the first result under the screen.
   */
  gaveWay: "The closest match to what you asked for comes first.",
  /**
   * The same in full, with why: the sentence that was given as the way the line should read.
   * It is said where the line is told to say it in full, and is a third line on a phone.
   */
  gaveWayInFull: "The things you asked for count the most, so the areas at the top are the closest match to them.",
  /**
   * Said in its place where a journey or a budget counts for more than anything that was
   * asked of the place. A person who asked for leafy and quiet must not read the first
   * result as the leafiest. It is short, so that the line stays two lines on a phone.
   */
  leads: (journeys: number, budget: boolean) =>
    journeys === 0
      ? "The budget counts the most here."
      : `The ${journeys === 1 ? "journey" : "journeys"}${budget ? " and the budget count" : journeys === 1 ? " counts" : " count"} the most here.`,
  /** A change of tenure takes the budget off: a rent is not a price (contract 5.3). */
  budgetWent:
    "Your budget was taken off, because what you can pay in rent is not what you can pay to buy. You can type a new one, or set it under Refine search.",
  /**
   * The same, where the search became a visit. A visit has no budget, so none can be typed
   * or set in its place: it says why the budget went, and what the areas are ranked by, as
   * the space requirements say it of a visit.
   */
  budgetWentForAVisit:
    "Your budget was taken off, because you are visiting and Burro does not ask what you can pay for a visit. It ranks the areas by everything else in your search.",
  /**
   * Said once a person has stopped a search that was their first, until the search next
   * moves: what was stopped, and what became of the words. The line said nothing, and
   * whoever could not see the page could not tell that the press had landed. It is two
   * lines of a phone and no more.
   */
  stopped: "Burro stopped, as you asked. No areas are ranked, and your words are still in the box.",
  /** The same over a search that is open: what was added to it is what was stopped. */
  stoppedOpen: "Burro stopped, as you asked. Your search is as it was, and your words are in the box.",
  nothingMatches: "No area passes every limit you set.",
  /**
   * Said in its place where no limit left any area out: every area has too little data for
   * what counts. It blamed the person, who had set no limit.
   */
  nothingRanked: "Burro could not rank any area, because it has too few figures for what counts in your search.",
} as const;

export const CHIPS = {
  /** The heading of the chips once words have been read into a search. */
  label: "What Burro understood",
  /** The heading before anything has changed the search: nobody said any of it. */
  startLabel: "Your search so far",
  /** The heading of a search that no words were read into: one made with the settings, or a shared one. */
  setLabel: "What is in this search",
  assumed: "assumed",
  /** In the row, after what was said of a thing: that the parts not shown were filled in, and by whom. */
  restAssumed: "Burro assumed the rest",
  /** The button at the end of the row, which shows the chips that are not in it. */
  rest: (count: number) => `+${count} more`,
  showFewer: "Show fewer",
  assumedHint:
    "Where a chip says \"assumed\", it is something you did not say, so Burro filled it in. You can change it by pressing the chip.",
  remove: "Remove",
  firm: "firm limit",
  flexible: "flexible",
  /**
   * The longest a journey may take, as a chip says it. Whether that is a firm limit is said
   * by the word after it, so this says the minutes and no more: "within" is one of the words
   * Burro itself reads as a firm limit, and it stood on a limit that was flexible.
   */
  within: (minutes: number) => `${minutes} minutes`,
  more: "more",
  fewer: "fewer",
  /** A scale, and the end of it that is asked for. Both names are the API's. */
  towards: (vibe: string, end: string) => `${vibe}: towards ${end}`,
  /** Asks for the other end of a scale. */
  turn: "Turn",
  turnTo: (vibe: string, end: string) => `Turn ${vibe} towards ${end}`,
  /** The word a vibe was read from, where the word has two meanings. The word is the API's spelling of it. */
  readFrom: (word: string) => `read from "${word}"`,
  hidden: "hidden",
  only: "only",
  off: "does not count",
  /** Said with the hints, where a journey or a budget counts for more than what was asked of the place. */
  leadsHint:
    "In this search a journey or the budget counts for more than what you asked of the area itself. If you would rather that counted the most, you can lower how much the journeys or the budget count under Refine search.",
} as const;

export const NOTICE = {
  label: "About your search",
  /**
   * Said once a search is open, where the settings stand under the part that refines it.
   * A way to try again stands beside it only where the words reached nothing that read
   * them, so the line does not speak of one.
   */
  degraded: `Burro could not read your words just now. You can choose what you want under ${REFINE.label}, which does the same job as typing.`,
  /** Said when the provider of the language model would not read what was typed. It names nobody. */
  refused: "The language model would not read this. Burro's rules have read it instead.",
  /** It gives a sentence that Burro reads whole, to show what it can read. The sentence names no place. */
  nothingRead: `Burro could not read anything in what you typed. It reads plain English, such as "leafy and quiet, near a park". You can say it another way, or choose what you want under ${REFINE.label}.`,
  nothingChanged: "Your search already says that, so nothing has changed.",
  /** Said when only a part of what was typed was read. */
  partUnread: `Burro read only some of what you typed, so the ranking leaves the rest out. You can say the rest again in shorter sentences, with one thing in each, or choose it under ${REFINE.label}.`,
  partShown: (at: number, of: number) =>
    of === 1
      ? "The words that Burro did not read are selected in the box."
      : `Burro did not read your words in ${of} places. The words in place ${at} of the ${of} are selected in the box.`,
  partNotFound: "Burro cannot show you which words they were.",
  /** Said while the browser has no connection. It is the reason given of a call that could not leave, too. */
  offline:
    "You are not connected to the internet at the moment. Your search is still here, so you can carry on when you are connected again.",
  /** Said after it, where a change is waiting to be sent. */
  offlineWaiting: "Burro will then send your last change.",
  /** Said after what failed, where results from before the failure are still on the page. */
  notUpdated: "The results below have not been updated, so they still show your search as it was before.",
  /**
   * Said under a space requirement whose change Burro has not answered, once a search is
   * open. What says what failed stands at the head of the page, with the button that tries
   * again, and a person who is among the space requirements does not see it: the control
   * shows what it was set to, and nothing in sight said that the results did not.
   */
  unsent: `Burro could not make this change just now, so the results do not show it yet. Burro will try again when you next change something, or when you press "${PROMPT.tryAgain}" at the top of the page.`,
  /** The same, while the browser has no connection: the change goes of itself once it has one. */
  unsentOffline:
    "You are not connected to the internet at the moment, so this change has not reached Burro and the results do not show it yet. Burro will send it when you are connected again.",
  /** Before the code of the request, which follows it on the same line. */
  requestId: "If you report this problem, please quote this reference:",
  /** Over the buttons that take out what the search names and Burro no longer has, one for each. */
  stale:
    "Your search includes something that is no longer in Burro's data, which can happen when the data has been brought up to date. Take it out with a button below, and Burro will rank the areas again.",
  takeOut: (what: string) => `Take ${what} out of my search`,
  thePlace: "the place",
  theArea: "the area",
  theSetting: "the space requirement",
} as const;

/**
 * Words for a call that gave no answer, when the reason is not the API's own. Each is said
 * in six places, of a search, a comparison, a link and the figures of an area, so none says
 * what it was that failed: the line beside it does. Nor does any say what to do, since the
 * button that tries again stands beside it wherever it is said. None blames what was typed.
 */
export const FAILURE = {
  timeout: "Burro took too long to answer.",
  network: "Burro could not be reached. The fault may be at Burro's end or in your connection.",
  offline: NOTICE.offline,
  not_configured:
    "This copy of the website is not connected to Burro's data, which means it cannot look anything up for you.",
  unreadable: "Burro sent back an answer that this page could not understand.",
  /**
   * Of an answer that is not Burro's own and says that too much was asked, as what stands
   * before Burro may answer. It says to wait, where no other line says what to do: the
   * button that tries again stands beside it, and pressed at once it is refused again.
   */
  busy: "Burro is busy at the moment, so it could not answer. Please wait a minute before you try again.",
  /** Of an answer that is not Burro's own and says that a fault was met. */
  fault: "Burro has a fault at the moment, so it could not answer.",
  aborted: "This was stopped before Burro had answered.",
} as const;

/**
 * One line for each kind of thing that was asked for and cannot be answered. What each
 * says Burro has no data on, or does not do, is a promise of what Burro does not do, and
 * is kept word for word. A search is open wherever one is said, so the settings are named
 * by the fold that holds them.
 */
export const UNMET: Readonly<Record<UnmetCategory, string>> = {
  broadband: "Burro has no data on broadband, so it has left that out of your search.",
  flood_risk: "Burro has no data on flood risk, so it has left that out of your search.",
  health_services:
    "Burro has no data on health services other than GP surgeries and pharmacies, so it has left that out of your search.",
  driving:
    "Burro does not work out journeys by car, so it has left that out of your search. It can work out a journey by public transport, by bike or on foot.",
  listings: "Burro does not show homes to rent or to buy. It ranks areas, so that you know where to look for a home.",
  affordability_verdict:
    "Burro does not say what you can afford. It shows what homes cost in each area, so that you can compare that with your own budget.",
  community_amenities:
    "Burro has no data on places of worship, or on shops and venues for one community, so it has left that out of your search.",
  outside_the_city: "Burro covers one city, so it has left out the place you named outside it.",
  street_cleanliness: "Burro has no measure of how clean a street is, so it has left that out of your search.",
  upkeep: "Burro has no measure of how well kept a place is, so it has left that out of your search.",
  ratings: "Burro has no ratings or reviews of any place, so it has left that out of your search.",
  prices_and_hours:
    "Burro has no data on what a place charges or when it opens, so it has left that out of your search.",
  mobile_coverage: "Burro has no data on mobile signal, so it has left that out of your search.",
  change_over_time: "Burro has no measure of how an area is changing, so it has left that out of your search.",
  other: `Burro could not read some of what you typed. You can say it another way, or choose what you want under ${REFINE.label}.`,
};

export const UNMET_LABEL = "What Burro could not answer";

export const REJECTED: Readonly<Record<RejectReason, string>> = {
  unknown_place: "Burro does not know that place.",
  unknown_area: "Burro does not cover that area.",
  not_in_release: "Burro has no figures to rank areas by that.",
  too_many_commutes: "Your search already has as many places as Burro can take, so remove one before you add another.",
  no_such_commute: "That place is not in your search.",
  out_of_range: "That number is outside what Burro accepts.",
  segment_not_for_tenure: "That kind of home does not go with the choice of renting, buying or visiting.",
  direction_not_allowed: "Burro can only count that one way, so it left it as it was.",
  // The one account of when recorded crime counts, as every page says it.
  crime_needs_explicit_request: CRIME_RULE,
  mismatched_choice: "That space requirement does not take that choice.",
  nothing_to_change: "Your search already says that.",
};

/**
 * Why an edit was not applied, as a page says it of one release. The rule on recorded crime
 * is followed by what is true of the release, where no vibe of it holds recorded crime.
 */
export function whyRefused(reason: RejectReason, meta?: Pick<MetaData, "tags" | "features">): string {
  return reason === "crime_needs_explicit_request" && meta !== undefined ? ruleIn(meta) : REJECTED[reason];
}

export const REJECTED_LABEL = "Changes Burro did not make";

/**
 * What Burro noticed in a sentence and left out of the search, and that some of the words
 * were not read: one line under what Burro understood, which names each thing and opens
 * to why. Nothing of it is offered, and nothing is asked. The name of each thing is the
 * API's. What counts recorded crime is said with the one account of when recorded crime
 * counts, as every page says it, and a thing the API gave no way to take in the API's words.
 */
export const LEFT_OUT = {
  /** The name of the notice, and what its one line begins with. */
  title: "Left out of your search",
  /** After the title, on its line: each thing by its name. Why is one press away. */
  named: (names: readonly string[]) => `: ${names.join("; ")}`,
  /** What the line calls the words that were not read, among what was left out. */
  words: "Some of your words",
  /**
   * What the line calls a thing whose name, as the API gives it, holds a figure: the amount
   * of a budget, or the minutes of a journey. What was typed is drawn in the box alone.
   */
  named_by_the_page: { budget: "What you can pay", commute: "A journey" },
  /**
   * What the line calls a rule for an area, by the name the API gives the area. The name
   * alone, after "Left out of your search", read as though the area had been left out of
   * the results: what was left out is what to do with it.
   */
  ofAnArea: (area: string) => `What to do with ${area}`,
  /**
   * What the line calls a journey that waits for a person, by the name the API gives its
   * place. The name alone read as though the place had been left out.
   */
  ofAJourney: (place: string) => `A journey to ${place}`,
  /** Why, of each kind of thing that the page has an account of its own for. */
  why: {
    residents: `This counts who lived in an area at the census of 2021, and Burro only counts that when you choose it yourself. You can add it under ${REFINE.label}.`,
    place: `Burro does not know the place you named, so it could not add the journey. You can name another place under ${REFINE.label}.`,
    /**
     * Of a number that the words gave and that is outside what Burro takes: the minutes of
     * a journey, or what can be paid. What was typed is drawn in the box alone, so it names
     * no number, and sends a person to where each box says what it takes.
     */
    range: `The number you gave is outside what Burro can take, so Burro has left it out of your search. You can set it under ${REFINE.label}, where each box for a number says the least and the most it takes.`,
    area:
      "Burro noticed the name of this area in your words, but it could not be sure what you want done with it. " +
      "Looking only in one area, or leaving one out, would take areas out of your results, so Burro does neither on a guess, and no area has been left out because of it. " +
      'If you want to look only in this area, you can type "only" and then its name. ' +
      "If you want to leave it out, you can hide it with the button on its result.",
    /**
     * Of what the service says waits for a person, where it counts neither recorded crime
     * nor who lived somewhere and the service says no more of why: a measure that a
     * decision holds to be offered and never applied, whoever asks. Which measure that
     * is, and what it follows, is the service's to say: so it names no thing and no
     * cause, and says what is true of each.
     */
    by_choice: `Burro noticed this in your words, but it is one of the things that Burro adds only when you choose it yourself, so it has left it for you to add. You can add it under ${REFINE.label}.`,
    /** Of a wish that the service says the words do not say is the person's own: it may be somebody else's. */
    not_said: `Burro noticed this in your words, but it could not be sure that you want it counted, so it has left it for you to add. You can add it under ${REFINE.label}.`,
    /** Of a journey that the service says waits for a person: the place may be somebody else's. */
    journey: `Burro noticed this place in your words, but it could not be sure that you need to reach it, so it has left the journey for you to add. You can add it under ${REFINE.label}.`,
    two_ways: `Burro could not tell from your words which way you want this to count, so it has left it out. You can add it under ${REFINE.label}.`,
    /** Of a thing that is read into words of which no reading was taken. */
    several: `Burro could read your words more than one way here, so it has left this out. You can add it under ${REFINE.label}.`,
    /**
     * Of a thing that is read into words that were taken another way. It names the chips
     * by their heading, which is where the way that was taken is seen.
     */
    otherwise:
      "Burro could read your words more than one way here. It took them one way, which is shown under " +
      `${CHIPS.label}, and left this one out so that the same words are not counted twice. You can add it under ${REFINE.label}.`,
  },
} as const;

/**
 * What an edit that was not applied was about, where that is a part of the search that the
 * API gives no name: a feature, a vibe, a place and an area are named by the API.
 */
export const REJECTED_PART = {
  tenure: KIND_OF_SEARCH.legend,
  budget: "Budget",
  journeys: "Journeys",
} as const;

/**
 * What stands wherever an estimate is shown: the service's line, word for word, which a
 * release that estimates its journeys serves with its form. A result takes it from the
 * fact of such a journey. It is kept here for where no such fact is in hand, and a test
 * holds it to the line as it was recorded.
 */
const ESTIMATED_FROM = "This is an estimate that Burro worked out from the distance, and not a time from a timetable.";

export const FILTERED: Readonly<Record<FilterReason, string>> = {
  excluded: "Hidden by you",
  not_selected: "Not one of the areas you chose",
  over_budget: "Over your budget, which is a firm limit",
  commute_cap: "A journey is longer than a firm limit",
  commute_likely_beyond: `A journey is likely beyond a firm limit. ${ESTIMATED_FROM}`,
};

/**
 * Why an area has no rank. Each is a label: it stands in the column of a table, beside a
 * count, and before what the area has no figure for, so it ends in no full stop.
 */
export const UNRANKED: Readonly<Record<UnrankedReason, string>> = {
  not_rankable: "Not ranked by Burro",
  insufficient_data: "Burro has too few figures for what counts in your search",
  character_unknown: "Burro knows too little of the character that counts in your search",
};

/**
 * Under the results: the areas that are not ranked, listed apart from those that are. The
 * name of an area and the name of each thing it lacks are the API's.
 */
export const APART = {
  /** On the button that opens the list. It is what says, before anything is pressed, that there are such areas. */
  title: (count: number) => (count === 1 ? "1 area could not be ranked" : `${count} areas could not be ranked`),
  label: "Areas that could not be ranked",
  lead: "Burro could not rank these areas, which is why they have no fit and no place in the list above. Each one says why. Where a figure is missing, Burro says so and does not fill it in.",
  /** Over the things an area has no figure for, each by the name the API gives it. It names their list too. */
  lacks: "What Burro has no figure for in this area",
} as const;

/**
 * A firm limit that could not be checked for an area, because the figure is missing. It
 * stands on a result before anything is opened, so each is one sentence. The area is
 * listed all the same: what cannot be checked leaves no area out.
 */
const NO_JOURNEY_TIME =
  "Your limit for a journey is firm, but Burro could not check it for this area, because it has no journey time.";

export const UNTESTED: Readonly<Record<FilterReason, string>> = {
  excluded: "Burro could not check whether you had hidden this area.",
  not_selected: "Burro could not check whether this is one of the areas you chose.",
  over_budget:
    "Your budget is a firm limit, but Burro could not check it for this area, because it has no cost figure.",
  commute_cap: NO_JOURNEY_TIME,
  commute_likely_beyond: NO_JOURNEY_TIME,
};

export const NOTHING_MATCHES = {
  title: STATUS.nothingMatches,
  /** The heading where no limit left any area out. */
  noData: "No area could be ranked.",
  lead: "Every area was left out, and these are the reasons why.",
  /** Over what the areas have no figure for, each by the name the API gives it. */
  lacks: "What Burro has no figure for",
  lacking: (name: string, count: number) => `${name}: ${count === 1 ? "1 area" : `${count} areas`}`,
  count: (count: number) => (count === 1 ? "1 area" : `${count} areas`),
  loosen: "Make a limit flexible",
  budgetFlexible: "Make the budget flexible",
  journeyFlexible: (place: string) => `Make the journey to ${place} flexible`,
  showHidden: (area: string) => `Show ${area} again`,
  showAll: (area: string) => `Stop showing only ${area}`,
} as const;

/** What opens the working of a result. The line under a list of more than five names it. */
const SHOW_THE_WORKING = "Show the working";

export const RESULTS = {
  title: "Results",
  /**
   * The name of the list, to whoever hears the page. It says the order and no more: where
   * nothing is set to rank by, no area is a closer match than the next.
   */
  listLabel: "Areas, in the order Burro ranked them",
  /** The list from the second result on. The first stands before the map, and the rest after it. */
  restLabel: "Areas, in the order Burro ranked them, from the second",
  /**
   * Under a list of more than five. Why an area fits is in the working of a result, since
   * a person who walked the website asked for it to go from the result itself: so the line
   * says where it is read.
   */
  firstFive: `Burro writes out why an area fits for the first five results only, and you can read it by pressing "${SHOW_THE_WORKING}" on any of them. For any other result, "${SHOW_THE_WORKING}" shows the figures behind its fit.`,
  waiting: "Your results will appear here once Burro has ranked the areas.",
  /** Under the first ten: the button that shows the rest of the list. */
  showMore: (count: number) => (count === 1 ? "Show 1 more" : `Show ${count} more`),
  /** Under the whole list, where areas are ranked below the last one listed. Both counts are the API's. */
  listed: (listed: number, ranked: number) =>
    `This list shows ${listed} of the ${ranked} areas that Burro ranked. You can find every one of them in the table of all areas.`,
  /** Opens the full working of a result, in place. */
  showWorking: SHOW_THE_WORKING,
  workingOf: (area: string) => `${SHOW_THE_WORKING}: ${area}`,
  /** Leads to the areas most like this one, on the area's own page. It is named as the fold it opens there. */
  moreLike: "More like this",
  moreLikeOf: (area: string) => `More like this: ${area}`,
  /** The heading of the reasons after the first, inside the working. */
  moreReasons: "More reasons why it fits",
  working: "Burro is working out the ranking again",
  fit: "Fit",
  fitOf: (score: number) => `${score} of 100`,
  rank: (rank: number) => `Rank ${rank}`,
  whereTitle: "Where it is",
  reasonsTitle: "Why it fits",
  /**
   * Under "Why it fits" and under "Trade-off", on a result, where the service gave none.
   * Each is said of what counts in the search and of nothing else, under the heading that
   * says what it is of. The second stands on the line of its heading on a phone, where a
   * longer one took a second line and stood the foot of the first result under the screen.
   */
  noReasons: "Burro found nothing that this area does well enough to give as a reason.",
  tradeOffTitle: "Trade-off",
  noTradeOff: "Burro found no trade-off.",
  reasonsFailed: "Burro could not load the reasons for this area this time.",
  detailsFailed: "Burro could not load the cost and the nearest station for this area this time.",
  /** Under a sentence a language model wrote. It says both: that a model wrote it, and that it was checked. */
  byModel: "This sentence was written by AI, and Burro then checked it against the source.",
  /**
   * What the key of a source is the source of, on a result: which sentence, and of which
   * area. It fills the gap of "Source for", so that no two keys of a page are named alike
   * and each can be spoken to: "Source for reason 1 for" an area, by the name the API gives.
   */
  sourceOfReason: (at: number, area: string) => `reason ${at} for ${area}`,
  sourceOfTradeOff: (area: string) => `the trade-off for ${area}`,
  openArea: (area: string) => `Open the page for ${area}`,
  hide: (area: string) => `Hide ${area} from my results`,
  showOnMap: (area: string) => `Show ${area} on the map`,
  actions: "Actions",
  /** Before the two codes at the foot of a list. The foot of every page names them the same. */
  foot: { release: "Version of the data", engine: "Version of the ranking" },
} as const;

/**
 * The lines under a result's name. The name of a vibe and the names of the ends of a scale
 * are the API's. "least" and "most" are the ends of a vibe that runs one way, as the
 * contract names them (section 7.3), and a test holds them to the facts.
 */
export const STRIP = {
  /**
   * The name of each list of lines, to whoever hears the page, which says what the list
   * holds: what was asked for, the rest of it where a narrow result folds its lines, the
   * vibes of an area where nothing was asked for, and the vibes nobody asked for where the
   * look has them stand under what was. The name of the area is the API's.
   */
  askedOf: (area: string) => `What you asked for in ${area}`,
  restOf: (area: string) => `More of what you asked for in ${area}`,
  label: (area: string) => `Vibes of ${area}`,
  othersOf: (area: string) => `Other vibes of ${area}`,
  least: "least",
  most: "most",
  band: (band: number) => `band ${band} of 5`,
  bands: (low: number, high: number) => `varies within this area, between band ${low} and band ${high} of 5`,
  /**
   * Which way the five bands run, said after the band: "band 4 of 5, from least to most".
   * It stands alone under the name of a vibe in a comparison too, so it is a few plain words.
   */
  from: (low: string, high: string) => `from ${low} to ${high}`,
  /** Said of a mark to a screen reader, in the name of its picture. */
  asked: "asked for",
  askedFor: (end: string) => `asked for: ${end}`,
  /**
   * Said once, where it can be seen, before the marks it is true of: the vibes that were
   * asked for, and then the others the area sits at an end of. Each stands on a line of its
   * own over the marks, so each is a few words: "Also" said nothing by itself. The first
   * stands in the narrow column of a name on a phone, where a third word is a second line
   * and the first result is no longer whole on the first screen.
   */
  group: { asked: "Asked for", also: "Other vibes" },
} as const;

export const COMPLETENESS = {
  // Not "what you asked for": the settings nobody chose count too, for less. Each is a
  // whole sentence and says what is counted, which is the fit: "Based on 9 of the 10
  // things" had no subject, and was read twice.
  all: "This fit is based on everything that counts in your search.",
  some: (present: number, asked: number) =>
    `This fit is based on ${present} of the ${asked} things that count in your search.`,
  /**
   * On a result, after how many things the fit is based on: how many of the things that
   * count are those nobody chose. A person who asked for four things read that ten count,
   * and nothing in sight said what the other six were. It names them as the bar of the
   * group that holds each does, "counted in every search", and the fold that holds them
   * as the fold names itself. It is no longer than it was: it stands on a result, where a
   * line more puts the foot of the first result under the screen of a phone.
   */
  usual: (count: number) =>
    count === 1
      ? `One of them is counted in every search. You can see and change it under ${REFINE.label}.`
      : `${count} of them are counted in every search. You can see and change them under ${REFINE.label}.`,
  /** The heading over the API's sentence for each thing the area has no figure for. */
  missingTitle: "What Burro has no figure for in this area",
  /**
   * On the result, in sight: what the area has no figure for, by the names the chips give.
   * An area with no figure for a thing that was asked for came first once, and the card
   * said only how many things the fit rested on. Such an area now stands below every area
   * that has the figure, and this line is what says which figure it has none for.
   *
   * It is one sentence, since it stands on a result before anything is opened. It reads
   * with one name and with several.
   */
  lacks: (names: readonly string[]) =>
    `Burro has no figure for ${named(names)} in this area, so the fit leaves ${names.length === 1 ? "it" : "them"} out.`,
  /** The same, of what the person asked for. It is said with the weight of a trade-off. */
  lacksAsked: (names: readonly string[]) => {
    const those = names.length === 1 ? "it" : "them";
    return `You asked for ${named(names)}, but Burro has no figure for ${those} in this area, so the fit leaves ${those} out.`;
  },
} as const;

export const JOURNEYS = {
  title: "Journeys",
  /**
   * The heads of the table, and the label of each cell where a narrow screen stacks its
   * rows. A time is named as a fact names it, less its first word: a cell here says
   * "21 minutes", where the figure of a fact is a bare number.
   */
  columns: {
    place: "To",
    how: "How",
    typical: "On a typical weekday morning",
    missed: "If you just miss a service",
    limit: "Your limit",
    /** Over the one cell that stands for both times, where there is no time to give. */
    time: "How long it takes",
  },
  minutes: (minutes: number) => `${minutes} minutes`,
  within: "within",
  over: "over",
  limit: (minutes: number) => `${minutes} minutes`,
  /** Beside a journey given as the trade-off, whose sentence gives the minutes and not the limit. */
  withinLimit: (minutes: number) => `Within your limit of ${minutes} minutes`,
  overLimit: (minutes: number) => `Over your limit of ${minutes} minutes`,
  beyond: (minutes: number) => `More than ${minutes} minutes`,
  /** In the cell of a journey that has no time. A comparison says it in the same words. */
  missing: "Burro has no journey time for this.",
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
  estimatedFrom: ESTIMATED_FROM,
  /**
   * Under two journeys or more: which of them the fit is worked out from. It
   * is the one that does least well against its own limit, which need not be
   * the one that takes the most minutes. The setting that chooses is named as
   * the settings name it, under the fold that holds them once a search is open.
   */
  usesOne: (place: string) =>
    `You named more than one place to reach. Only the journey to ${place} counts towards the fit, because it is the one that does least well against the limit you set for it. If you would rather Burro used the average of your journeys, you can change "${JOURNEY.combine}" under ${REFINE.label}.`,
  usesMean: `The fit uses the average of your journeys. If you would rather it used only the journey that does least well against its limit, you can change "${JOURNEY.combine}" under ${REFINE.label}.`,
  /**
   * Directly under the fit, where the journeys count for nothing in it: the ranking has no
   * figure for their share of the fit, because Burro has a time for none of them. A person
   * who named a workplace must not read the fit as if it had weighed it. It is one sentence,
   * since it stands on a result before anything is opened.
   */
  notCounted: (journeys: number) =>
    journeys === 1
      ? "Your journey does not count towards this fit, because Burro has no journey time for it from this area."
      : "Your journeys do not count towards this fit, because Burro has no journey time for any of them from this area.",
  /** Under the journeys, in place of the line that says which of them the fit is worked out from. */
  usesNone: (journeys: number) =>
    journeys === 1
      ? "This journey does not count towards the fit, because Burro has no journey time for it from this area."
      : "None of these journeys counts towards the fit, because Burro has no journey time for any of them from this area.",
  /** The link under the journeys, to what a typical morning and just missing a service mean. */
  timed: "How journeys are timed",
  notGiven: "Not given",
  notApply: "Does not apply",
} as const;

/**
 * The cost of a result. Each figure is named as the page of an area names it, so that a
 * person who goes from one to the other reads one thing one way. Where a budget falls is
 * said, and what that means for a person is not: that would be a figure with no source.
 */
export const COST = {
  title: "What homes cost",
  none: "Burro has no cost figure for this kind of home in this area.",
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
  what: "What this figure is",
  middleOfAll: "The middle price of all homes of this kind, whatever their size",
  soldIn: "Homes sold in",
  /** How many sales a price that was counted is based on. The count is the API's. */
  sales: "Number of sales it is based on",
  pictureOfOne: "The middle price, with your budget marked beside it",
  belowMiddle: "Your budget is below this middle price.",
  aboveMiddle: "Your budget is above this middle price.",
  atMiddle: "Your budget is the same as this middle price.",
  // A rent that is of a wider place than the area. The place, the months and the count are
  // slots of the fact, and no figure is drawn without them.
  figureOf: "This figure is for",
  recordedIn: "Rents recorded in",
  rents: "Number of rents it is based on, to the nearest ten",
  pictureOfRent: "The range of rents of the place, with the middle and your budget marked on it",
  belowMiddleRent: "Your budget is below this middle rent.",
  aboveMiddleRent: "Your budget is above this middle rent.",
  atMiddleRent: "Your budget is the same as this middle rent.",
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

/** The head of the column that says what a thing adds. The line under the table names it. */
const ADDS_TO_THE_FIT = "Adds to the fit";

export const BREAKDOWN = {
  title: "How the fit is worked out",
  /**
   * Three figures stand side by side in the table, and the caption is the one place that
   * says how they differ: how much a thing counts is where its slider is set, its share is
   * what that gives it of the fit, and what it adds is what the area earns of that share.
   */
  caption:
    "This table lists everything that counts in your search. For each thing it gives how much it counts, the share of the fit that this gives it, and how much it adds to the fit of this area.",
  columns: {
    thing: "What counts",
    weight: "How much it counts",
    share: "Its share of the fit",
    adds: ADDS_TO_THE_FIT,
    says: "The figures for this area",
  },
  journey: "Journey",
  budget: "Budget",
  /** There is a figure, and the fact that holds it is not in hand to show. */
  has: "Has a figure",
  hasNot: "No figure",
  outOf: (value: number) => `${value} of 100`,
  percent: (value: number) => `${value}%`,
  roundedDown: `Burro rounds every figure in this table down to a whole number. This means that the figures under "${ADDS_TO_THE_FIT}" can come to a little less than the fit when you add them up.`,
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
  /** The name of the two pictures together, to whoever hears the page. The name of the area is the API's. */
  title: (area: string) => `Two small maps that show where ${area} is`,
  /** Under the first picture: every area as one shape, with a mark where this one stands. */
  city: "Among all the areas Burro covers",
  /** Under the second: the area drawn close, among those around it. */
  close: "Among the areas around it",
} as const;

