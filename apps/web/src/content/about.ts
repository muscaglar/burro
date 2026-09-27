/**
 * Site copy for the key to the drawings, which stands first on the page of vibes: every
 * drawing and mark a visitor meets anywhere on the website, each with what it means in a
 * sentence or two. What a town is built of is a part of the key, and its words are in
 * `town.ts`. Every other word of the pages that explain is in the file of its own page,
 * and every word about a vibe, a measure or a source is the API's.
 *
 * It is written for somebody who has never seen Burro, in whole sentences that say what
 * follows from what.
 *
 * Nothing here names a vibe, a measure or a place, and nothing here says anything of one.
 * It states no figure of its own but how many shades and steps there are, and how many
 * results bear a pin, which a test holds to where each is set.
 *
 * It holds what is drawn today. A drawing that is added to the website is added here, and
 * one that goes from every page goes from here with it.
 */

import { KNOWN } from "./kit";
import { TAKEN } from "./taken";

/** What a trade-off is, whichever drawing stands beside it. */
const TRADE_OFF =
  "A trade-off is one thing that counts in your search where the area falls short of what you asked for, so it is what you would give up in return for the rest. Where an area falls short on several things, the result gives the one that weighs most.";

export const ABOUT = {
  key: {
    title: "Key to the drawings",
    lead: "Burro uses small drawings in place of long labels. Each one is shown here at the size you will meet it, with what it means beside it.",

    /**
     * The parts of the key, at its head: each by the name its part bears, with a drawing or
     * two of what it holds, so that a drawing is found without reading every row. To a
     * visitor each is a section of the key.
     */
    contents: {
      /** What the list of them is, to whoever hears the page. */
      label: "The sections of the key",
      lead: "The key has five sections, one for each place where you will meet a drawing. Press a section to go straight to it.",
    },

    /** The things of a search: the vibes, what else can be asked for, and what is done with one. */
    things: {
      title: "The things in a search",
      vibes:
        "Every vibe has a small drawing of its own, which stands beside the name of the vibe wherever it appears. You can press a name here to read about that vibe further down this page.",
      /** What the list of the vibes is, to whoever hears the page. */
      vibesList: "The drawing of each vibe",
      others: "The other things you can ask for have drawings too, so that you can tell them apart at a glance.",
      /** What the list of them is, to whoever hears the page. */
      othersList: "The drawing of each other thing",
      kinds: {
        place: "A journey to a place you need to reach",
        budget: "What you can pay",
        tenure: "Whether you are renting, buying or visiting",
        home: "The size or type of home",
        area: "An area you named, to keep to it or to leave it out",
      },
      off: "A drawing in outline, with its colour taken away, means the thing is still in your search but counts for nothing. This happens when you turn something all the way down without removing it.",
      gauge:
        "A row of blocks that fills from the left shows how much a thing counts in your search. The more blocks are filled, the more that thing moves the ranking.",
      gaugeOfAScale:
        "A vibe with two ends has a post in the middle of its row, and the blocks fill from the post towards the end you asked for.",
      /**
       * The groups the things of a search are gathered in, each with the drawing of its bar.
       * What a group is called is the API's, or site copy for a code of the API's.
       */
      groups:
        "Under Space requirements the things you can ask for are gathered in groups, and each group has a drawing of its own on its bar. A measurement that goes into no vibe takes the drawing of its group.",
      /** What the list of the groups is, to whoever hears the page. */
      groupsList: "The drawing of each group",
      /** What Burro does with a sentence is said here, beside the cross of the chip it makes of each thing. */
      cross: TAKEN.chip,
    },

    /** What else is drawn on a result, and on any page of the website. */
    result: {
      title: "On a result and across Burro",
      /** It is drawn beside an example and beside a place that matches, and nowhere else: Burro asks nothing. */
      carrot:
        "A carrot lies beside the choice you are on in a list, such as the examples under the search box or the places that match a name you typed.",
      rank: "The number on a flag is the place a result took in the ranking for your search. Every flag is drawn the same, because the first result is the closest match to what you asked for, and has not won anything.",
      source:
        "A key opens the source of a figure. When you press it, Burro shows where the figure comes from and the date it is from.",
      /**
       * What stands beside the trade-off of a result, which was drawn two ways: a row of
       * the key draws the one a result draws, and says what that one is. What a trade-off
       * is, is the engine's to say: one thing that counts and that the area does not do
       * as was asked, and of several the one that takes most from its fit.
       */
      tradeOff: {
        scales: `A pair of scales marks the trade-off of a result. ${TRADE_OFF}`,
        arrows: `Two arrows, one pointing each way, mark the trade-off of a result. ${TRADE_OFF}`,
      },
      arrow:
        "An arrow at the end of a bar marks a part of the page that you can open and close by pressing the bar. The arrow points down while the part is closed and up while it is open.",
      notice:
        "A band of amber marks a note that Burro wants you to read, such as the line that names what it left out of your search.",
      /** Under it, in the same row: what Burro never takes for a person, and why, as the methods say it. */
      never: TAKEN.left,
      fault:
        "A band of red marks something that went wrong, such as a search that could not reach Burro. The words beside it say what happened.",
    },

    /** What is drawn on the map. */
    map: {
      title: "On the map",
      pin: "A numbered pin stands on each of the first ten results, and its number is the place that area took in the ranking.",
      greens:
        "Land is drawn in five shades of green. After a search, a darker green means a closer match to what you asked for. Where a map is coloured by a vibe, a darker green means more of that vibe, or nearer to its second end.",
      sand: "Land the colour of sand has no match to show, which is how every area is drawn before a search.",
      dots: "Dots mean that Burro could not rank the area, or could not work the vibe out for it. This happens when too little is known about the area, and Burro says so rather than guess.",
      lines:
        "Slanted lines mean that the area was left out of the ranking, either by a firm limit you set, such as a budget or a journey time, or because you chose to hide it.",
      water: "Blue is water.",
    },
  },

  /**
   * In the key: how a band is drawn, state by state, each line beside the drawing it is
   * of. What a band is, and when an area is placed on a vibe, are said in `vibes.ts`: this
   * says what is seen. The drawing of each state says its band in words, in the words
   * every band is said in.
   */
  band: {
    title: "Where an area sits on a vibe",
    lead: "Wherever Burro shows where an area sits on a vibe, it draws a gauge. A gauge is five steps with a peg on one of them, and a small picture at each end. A peg further along means more of the thing, and not that the area is better.",
    /**
     * After what a gauge is, where the two pictures of every vibe stand with the vibe alone:
     * what the two mean, where they are, and that neither end is the better one.
     */
    pictures:
      "Every vibe has two small pictures of its own, one for each end of its gauge, and they are shown with each vibe further down this page. The first picture shows little of the thing and the second shows much of it, or, where a vibe runs between two opposites, each shows what that end is. A picture says what an end is and nothing more, because neither end of a gauge is the better one.",
    states: {
      oneWay:
        "Most vibes run one way, from least to most. The peg stands on the step where the area sits among all the areas that were compared. On the page of an area the words beside the gauge say the same, such as \"around the middle\".",
      scale:
        "Some vibes run between two opposites, and these have the name of each end under its picture. Neither end is the better one.",
      /**
       * Over the two pictures of every vibe, where the key has them: what the two mean, and
       * that neither end is the better one.
       */
      ends:
        "Every vibe has two small pictures of its own, one for each end of its gauge, and each pair is shown here beside the name of its vibe. The first picture shows little of the thing and the second shows much of it, or, where a vibe runs between two opposites, each shows what that end is. A picture says what an end is and nothing more, because neither end of a gauge is the better one.",
      part: `A chequered mark with the words "${KNOWN.some}" means that some of the measurements behind the vibe are missing for the area, so Burro worked the vibe out from the ones it has. The step the peg stands on is chequered in the same way, and the page of the area says how many of the measurements Burro used.`,
      mixed:
        "A bar across several steps, with no peg, means that the homes of the area differ a good deal from one another. They span three steps or more, so the area sits at no one point.",
      unplaced:
        "Five empty steps with no peg mean that Burro could not work the vibe out for the area, because too many of the measurements it needs are missing. Rather than guess, Burro leaves the steps empty, and it never draws such an area in the middle or as the least.",
    },
    /** What the list of the five bands is, to whoever hears the page. */
    five: "The five steps, from least to most",
    /** What the list of the two pictures of every vibe is, to whoever hears the page. */
    pairs: "The picture at each end of the gauge of each vibe",
    /** Between the names of the two ends of a vibe, where they are said to whoever hears the page. */
    to: "to",
  },
} as const;
