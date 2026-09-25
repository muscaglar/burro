/**
 * Site copy for the accessibility statement. It says what is checked, what
 * has not been tested, and how to report a problem.
 *
 * It must stay true. When a check below is made by hand, move it from
 * `notTested` to `checked` and say when. Do not claim what has not been done,
 * and when a fault is found that is not yet put right, say so under `short`.
 */

export const ACCESSIBILITY = {
  title: "Accessibility statement",
  lead: "Burro aims to meet the Web Content Accessibility Guidelines, version 2.2, at level AA. It has not been audited, and parts of it have not been tested with the tools people use.",
  updated: { label: "Last updated", date: "2026-09-25" },

  built: {
    title: "What the website is built to do",
    points: [
      "Every map has a table that says everything the map shows. It is one press from the map. On a narrow screen each area of the table is a block, and each thing said of it says what it is.",
      "An area is named on the map where there is room for its name. The names are for the eye: they take no press, and the table holds every one of them.",
      "Everything works by keyboard. Focus is always visible, and is never left on nothing: what is removed passes it to what is beside it.",
      "When you press Search, what Burro made of your words is drawn directly under the box you typed in, and is said to a screen reader.",
      "A results page opens with the answer first and everything else closed. On a narrow screen the first result stands directly after what Burro understood, and the map after the first result. What opens, opens in place, and Escape closes it.",
      "What Burro understood is drawn as chips that wrap, so that none is cut off or scrolled out of sight. What was asked for by way of character comes first.",
      "Where an area sits on a vibe is drawn as five cells. On a result each drawing says its band in words to a screen reader, and whether the vibe was asked for. On the page of an area and in a comparison the band is written in words beside the drawing, for everyone.",
      "What Burro read in your words and did not apply is offered as buttons, and nothing is added until you press one. Each offer says what it would do, shows the words of yours it rests on, and says what follows. Where Burro reads a thing one way, that way is marked in words as its guess.",
      "The map can be skipped, and skipped to.",
      "Colour is never the only signal. Rank, fit and status are always given in words or figures.",
      "A control is at least 24 pixels wide and high, and the main controls are 44.",
      "A slider has buttons beside it, so nothing needs dragging. A slider that runs from 0 to 100 has a number field as well. One that runs between two named ends has a button at each end.",
      "Nothing moves if your system asks for reduced motion.",
      "Text can be made larger, and the page follows your system's light or dark setting.",
      "The page of an area reads with scripts switched off, with the source and the date under every figure, but for the census figures. It opens with where the area sits on each vibe. What is long is closed until it is pressed, and opens with scripts switched off.",
      "The page of vibes reads with scripts switched off. On a narrow screen each part of a recipe is stacked, and each thing said of it says what it is.",
      "A comparison is a table. On a narrow screen each row is stacked, and each figure says which area it is of.",
      "The journeys of a result, and how its fit is worked out, are tables too. On a narrow screen each row is stacked, and each figure says what it is.",
      "Nothing is dimmed to show a state. That results are being worked out again is said in words.",
      "What explains the chips, the results, the settings and the map is drawn where it can be seen, and is not kept for a screen reader alone. That goes for what 0 and 100 mean on a slider. What explains the chips is drawn once a chip or the row of them is opened.",
      "The areas chosen to compare stay at the foot of the screen. The page scrolls what takes the focus clear of them.",
      "The census figures of an area are tables, each with a caption that says what it is, when it was counted and where. Each is closed under its own name until it is pressed. A row under a group is read out with the name of its group. The drawing beside a share says nothing the table does not, and is kept from a screen reader. On a narrow screen each row is stacked, and each figure says whose it is.",
    ],
  },

  checked: {
    title: "What is checked automatically",
    points: [
      "The contrast of every colour pair, in light and in dark, against the ratio it needs.",
      "The structure of each page: headings, landmarks, labels, names and roles.",
      "That a search can be made and refined with the keyboard alone, in a browser stood in for by software.",
      "That every slider can be set without dragging, and that every control is given one of the two sizes.",
      "That the table beside the map holds every area, with its rank, its fit and the reason it has none.",
      "That areas can be chosen and compared, and a search shared, with the keyboard alone, in a browser stood in for by software.",
      "That the page of an area, as it is built, holds every figure with its source and its date, and nothing that needs a script to be read but the census figures, of which it holds none.",
      "That the page of an area, before anything is opened, opens with where the area sits on each vibe, ends with where to go and look, and draws no more than was measured in a browser.",
      "Every page as it is built: that it says what language it is in, has a title of its own, has its headings in order, and gives a name to every link, field, button and table.",
      "That no style draws anything see-through, so that every colour is drawn at the contrast that was worked out for it.",
      "That a table which is stacked on a narrow screen still says the role of each of its parts.",
      "That the focus is passed on when a chip, a question, a word of the shelf, a suggestion or the card of the map goes, and that no button is switched off while it may have the focus, in a browser stood in for by software.",
      "That a results page, before anything is opened, holds ten results at most and nothing that is open.",
      "That a box which scrolls sideways cannot make the page itself wider than the screen.",
      "That no style moves or resizes anything because the focus or the pointer came or went, so that a press lands where it was aimed.",
      "That the census figures of an area are drawn as tables with their captions and headings, in the order they came, in one colour, with nothing in them to sort or filter by.",
    ],
  },

  short: {
    title: "What is known to fall short",
    points: [
      "The page shown when the server fails before anything is drawn is not Burro's own. It does not say what language it is in, and it is not in Burro's words. It shows no figure and names no place.",
      "Which end of a scale was asked for is drawn in heavier letters on a result, and said in words to a screen reader. For the eye, the words are on the chip above the results and not on the result.",
      "On a narrow screen a result draws the vibes that were asked for, and not the two others the data chose for it. They are on the page of the area, one press from its name.",
      "Once a search is open, the title of the page and the heading of the results are kept for a screen reader and are not drawn, so that the first result is whole on the first screen of a phone.",
      "A sentence may be read only in part. The page says so under the box and can select the part that was not read, but it cannot yet say why it was not.",
      "In the dark theme, two swatches of the map's legend were once seen drawn in light colours, in a browser that was imitating dark. It has not been seen with a system set to dark.",
      "The census figures of an area are not in the page as it is built. They are asked for when that part is opened, which needs scripts to be on, and the page says so where they are off.",
    ],
  },

  notTested: {
    title: "What has not been tested",
    lead: "None of these has been checked by a person yet. Each will be, before the website opens to the public.",
    points: [
      "Use with a screen reader.",
      "Text at 200% zoom.",
      "Reflow on a screen 320 pixels wide.",
      "Forced colours and high contrast modes.",
      "The real size of each control on a touch screen.",
      "The map, used by keyboard alone.",
      "The comparison of areas on a narrow screen, where its rows are stacked.",
      "The table of every area on a narrow screen, where each area is a block. It was laid out in a browser at the width of a phone, and not on a phone.",
      "The names of the areas on the map, at text sizes other than the one the website sets.",
      "The journeys of a result and how its fit is worked out, on a narrow screen, where their rows are stacked.",
      "The shelf of words, the choices Burro offers when it was not sure, and a slider with two named ends, with a screen reader or on a touch screen.",
      "The page of an area, with a screen reader or on a touch screen: the line of each vibe, which opens what it is made of, and the parts of the page that are closed until they are pressed.",
      "The page of vibes on a narrow screen, where the parts of each recipe are stacked.",
      "Whether the areas chosen to compare, which stay at the foot of the screen, ever cover what has the focus. It was checked by software in a browser, and not by a person at a keyboard.",
      "Copying the link to a shared search, in a real browser.",
      "The census figures of an area, with a screen reader, at 200% zoom, in forced colours and in the dark theme. They were opened by keyboard in a browser at the width of a desk and of a phone.",
    ],
  },

  report: {
    title: "How to report a problem",
    // There is no address yet. Do not invent one. It says nothing of whether the data is
    // made up: the statement is drawn on every release, and the banner says what is shown.
    noAddressYet:
      "There is nowhere to send a report yet. This is a test release. An address will be given here before the website opens to the public.",
  },
} as const;
