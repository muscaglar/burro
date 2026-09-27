/**
 * Site copy for the town of an area: the small drawing that is built by rule from four of
 * the area's vibes.
 *
 * A town is a drawing made from four figures, and is no picture of a place. `line` says so,
 * and stands with every town, in sight. `short` says the same two things in fewer words,
 * where a town stands with little room. The rest says what each part of the drawing is
 * made of, to whoever hears the page and to whoever reads the key.
 *
 * It is written for somebody who has never seen Burro, in whole sentences that say what
 * follows from what.
 *
 * No word here names a vibe or a place. The name of a vibe and the names of its ends are
 * the API's, and the words for a band are in `bands.ts` and in `search.ts`.
 */

export const TOWN = {
  /** With every town, in sight. A town never stands without it. */
  line: "This little town is a drawing based on four of the area's vibes. This means it shows the character of the area, and is not a picture of what the place looks like.",
  /**
   * The same in fewer words, where a town stands with little room: at the head of the page of
   * an area on a narrow screen, over what the area is like. It says both things the line says:
   * what a town is drawn from, and that it is no picture of the place. What follows from that
   * is said in full in the key to the drawings.
   */
  short: "This little town is a drawing based on four of the area's vibes, and not a picture of the place.",

  /** What the drawing is, to whoever hears the page, before what it is made of. */
  name: "A little town, drawn from four vibes",
  /** The same, where the page says whose it is. The name of the area is the API's. */
  nameOf: (area: string) => `A little town, drawn from four vibes of ${area}`,

  /** The parts of the drawing, as the head of what is said of each. */
  parts: {
    trees: "Trees",
    height: "Height of the buildings",
    lit: "Lit windows",
    roofs: "Roofs",
  },
  /** The same, in a list. */
  listed: {
    trees: "trees",
    height: "buildings",
    lit: "lit windows",
    roofs: "roofs",
  },

  /** A part that is drawn: the vibe it is drawn from, and where the area sits on it. Both are given. */
  drawn: (vibe: string, where: string) => `${vibe}, ${where}`,
  /** A part of a mixed area, which sits at no one point. It is drawn from its band, and says so. */
  mixed: (vibe: string, range: string, band: string) => `${vibe}, ${range}. It is drawn as ${band}`,

  /** What is left blank of each part. */
  blank: {
    trees: "No tree is drawn",
    height: "No building is drawn",
    /** The windows of a building are drawn with it, so what is blank of them is their light. */
    lit: "Every window is dark",
    roofs: "No roof is drawn",
  },
  /** The same of what is drawn on a building, where no building is drawn. */
  blankUnbuilt: {
    lit: "No window is drawn",
    roofs: "No roof is drawn",
  },
  /** What is blank, and why. */
  because: (blank: string, why: string) => `${blank}, because ${why}`,
  /** Why a part is blank: the area cannot be placed on its vibe. The name of the vibe is the API's. */
  notKnown: (vibe: string) => `${vibe} could not be worked out for this area`,
  /** Why a part is blank, where Burro has no such vibe, and so no name for it. */
  notHeld: "Burro does not have the vibe it is drawn from yet",
  /** Why a part that is known is not drawn: it is drawn on a building, and no building is drawn. */
  unbuilt: (vibe: string) => `${vibe} is known, but there is no building to draw it on`,
  /** Why a part is blank whatever is known of it: nobody asked for a town, and recorded crime is shown only when asked for. */
  countsCrime: (vibe: string) => `${vibe} counts recorded crime, which is shown only where you ask for it`,

  /** Under the line, in sight, where any part is not drawn: which. */
  leftBlank: (parts: readonly string[]) => `Burro has left part of this town blank: ${parts.join(", ")}.`,
  /** After it, why a part may be blank: a sentence for each reason that holds of the town. */
  whyBlank: {
    unknown: "It leaves a part blank when it could not work out the vibe behind it, rather than guess.",
    crime: "Recorded crime is drawn only where you ask for it, so a part whose vibe counts it is left blank.",
    /** Of a window and a roof that are known, where the buildings are not drawn. */
    unbuilt: "Windows and roofs are drawn on buildings, so where no building is drawn they are left out too.",
  },

  /** Over the parts, where they are written out under the drawing. */
  madeOf: "What it is drawn from",

  /** In the key to the drawings: what each part of a town is, from one end of its vibe to the other. */
  key: {
    title: "What a town is built of",
    lead: "Beside the name of an area you will often see a little town. Each little town is a drawing based on four of the area's vibes. This means it shows the character of the area, and is not a picture of what the place looks like. Every town is the same size, and neither end of a vibe is the better one.",
    /** Over the rows: what the two towns of each row are. */
    ends: "For each of the four vibes, the two towns below show an area at one end of the vibe and at the other.",
    /** After the name of a vibe, which is the API's: what it is, in a town. */
    is: {
      trees: "is drawn as the trees.",
      height: "is drawn as the height of the buildings.",
      lit: "is drawn as the windows that are lit.",
      roofs: "is drawn as the roofs.",
    },
    /** In place of the name of a vibe that Burro does not have, and so has no name for. */
    noVibe: "A vibe Burro does not have yet",
    /** Beside a vibe that Burro can work out for no area: what becomes of its part, in every town. */
    notYet: "Burro cannot work this vibe out for any area yet, which means this part is left blank in every town.",
    /** Beside a vibe whose recipe holds recorded crime. Nobody asks for a town, so no town is drawn from it. */
    countsCrime:
      "This vibe counts recorded crime, which is shown only where you ask for it. Nobody asks for a town, so this part is left blank in every town.",
    notKnown: "What is not known",
    isBlank: "is left blank.",
    blank: "Where Burro could not work out one of these vibes for an area, it does not draw that part of the town: no tree, no building, no roof, or every window dark. It never draws the middle or the least in its place, because that would be a guess.",
  },
} as const;
