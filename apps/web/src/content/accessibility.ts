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
  updated: { label: "Last updated", date: "2026-09-23" },

  built: {
    title: "What the website is built to do",
    points: [
      "Every map has a list or a table beside it that says everything the map shows.",
      "Everything works by keyboard. Focus is always visible, and is never left on nothing: what is removed passes it to what is beside it.",
      "When you press Search, what Burro made of your words is drawn directly under the box you typed in, and is said to a screen reader.",
      "The map can be skipped, and skipped to.",
      "Colour is never the only signal. Rank, fit and status are always given in words or figures.",
      "A control is at least 24 pixels wide and high, and the main controls are 44.",
      "A slider has buttons and a number field beside it, so nothing needs dragging.",
      "Nothing moves if your system asks for reduced motion.",
      "Text can be made larger, and the page follows your system's light or dark setting.",
      "The page of an area reads with scripts switched off, with the source and the date under every figure.",
      "A comparison is a table. On a narrow screen each row is stacked, and each figure says which area it is of.",
      "The journeys of a result, and how its fit is worked out, are tables too. On a narrow screen each row is stacked, and each figure says what it is.",
      "Nothing is dimmed to show a state. That results are being worked out again is said in words.",
      "What explains the chips, the results, the settings and the map is drawn where it can be seen, and is not kept for a screen reader alone. That goes for what 0 and 100 mean on a slider.",
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
      "That the page of an area, as it is built, holds every figure with its source and its date, and no button that must be pressed to read one.",
      "Every page as it is built: that it says what language it is in, has a title of its own, has its headings in order, and gives a name to every link, field, button and table.",
      "That no style draws anything see-through, so that every colour is drawn at the contrast that was worked out for it.",
      "That a table which is stacked on a narrow screen still says the role of each of its parts.",
      "That the focus is passed on when a chip, a question or the card of the map goes, and that no button is switched off while it may have the focus, in a browser stood in for by software.",
      "That a box which scrolls sideways cannot make the page itself wider than the screen.",
    ],
  },

  short: {
    title: "What is known to fall short",
    points: [
      "The page shown when the server fails before anything is drawn is not Burro's own. It does not say what language it is in, and it is not in Burro's words. It shows no figure and names no place.",
      "The table of every area is not stacked on a narrow screen. It may be wider than the screen, and then scrolls sideways inside its own box. The page itself does not.",
      "A place you named may be shown as a number and not by its name. The page says so where it happens.",
      "A sentence may be read only in part. The page says so under the box and can select the part that was not read, but it cannot yet say why it was not.",
      "In the dark theme, two swatches of the map's legend were once seen drawn in light colours, in a browser that was imitating dark. It has not been seen with a system set to dark.",
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
      "The journeys of a result and how its fit is worked out, on a narrow screen, where their rows are stacked.",
      "Copying the link to a shared search, in a real browser.",
    ],
  },

  report: {
    title: "How to report a problem",
    // There is no address yet. Do not invent one.
    noAddressYet:
      "There is nowhere to send a report yet. This is a test release on made-up data. An address will be given here before the website opens to the public.",
  },
} as const;
