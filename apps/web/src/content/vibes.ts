/**
 * Site copy for the page of vibes. It says what a vibe is and how one is worked
 * out, in words that stay true whatever release is loaded. Every vibe, its
 * meaning, what goes into it, its sources and what it cannot see come from the
 * API, so the page can never disagree with the engine.
 *
 * It is written for somebody who is choosing where to live and has never seen
 * Burro: in whole sentences that say what follows from what. What is said of
 * each vibe in sight is short. How Burro works a vibe out is one press away,
 * under the vibe, and nothing of it is lost.
 *
 * The one number written here is a rule of the method that no route serves:
 * how much of what goes into a vibe an area must have a figure for. A test
 * holds it to the contract.
 *
 * One thing has one name here and on every other page. What a vibe is worked out
 * from is "what goes into it", and what it cannot tell is "what it cannot see".
 * Where Burro has too few figures it "could not work out" the vibe for an area:
 * it is never said to place an area, which is a word of the design.
 */

const WORKED_OUT =
  "Burro works each one out from measurements of the area, which means you can always see what went into it and what it leaves out.";

/** What opens all that is said of how a vibe is worked out. The page names it where it says what it opens. */
const WORKS = "How Burro works this out";

export const VIBES = {
  title: "Vibes",
  /**
   * What the page is for. It names two vibes as examples, by the names the API gives
   * them, so that it names none the data does not hold.
   */
  lead: (examples: readonly string[] = []): string => {
    const [first, second] = examples;
    return first === undefined || second === undefined
      ? `A vibe is a way of describing what an area feels like. ${WORKED_OUT}`
      : `A vibe is a way of describing what an area feels like, such as ${first} or ${second}. ${WORKED_OUT}`;
  },
  /** The same with the founder's own two examples, which are written here and not read from the data. */
  leadAsWritten: `A vibe is a way of describing what an area feels like, such as leafy or well connected. ${WORKED_OUT}`,
  /** After it: how the page is laid out, so that the key is found and the vibes after it. */
  order: "This page begins with a key to the drawings you will meet across Burro. After the key, each vibe is described in turn.",

  /** Over the vibes, after the key. */
  each: {
    title: "The vibes, one by one",
    lead: "Each vibe has a short description and a small map of the city coloured by it. On every map a darker green means more of the vibe, and where a vibe runs between two opposites, a darker green means nearer to the second of them. An area drawn with dots is one that Burro could not work the vibe out for.",
    residents:
      "Most vibes describe the area itself. A vibe that also counts who lived in an area says so in its description, and it counts their age or their households and nothing else.",
    more: `If you would like to know what goes into a vibe and what it cannot see, open "${WORKS}" under it.`,
  },

  /** It is said of which vibe to whoever hears the page. */
  works: WORKS,

  how: {
    title: "How Burro works out a vibe for an area",
    points: [
      "Each vibe is worked out from several measurements, and each measurement has a share that says how much it counts. The shares of a vibe add up to 100. For some measurements a higher figure counts towards the vibe, and for others a lower one does.",
      "Burro then sorts the areas into five bands, which the key draws as five steps. An area's band says where it sits among the areas compared, in fifths: band 1 is the fifth nearest the low end, and band 5 is the fifth nearest the high end. Areas that are level share a band.",
      "Burro gives an area a band only when the area has a figure for measurements that carry 60 of the 100 shares. With fewer, Burro says that it could not work the vibe out for the area, and never puts it in the middle as a guess.",
      "Where the homes of one area span three bands or more, the area is said to vary within itself, and it is drawn as a bar across those steps.",
      "A vibe is never shown as a percentage, a score or a rank, because five bands is as fine as its measurements allow.",
      "Burro chose which measurements go into each vibe and how much each one counts, and that choice is a judgement. No language model writes or scores a vibe.",
    ],
  },

  /**
   * The two ends of a vibe that runs between two, under what it means: "Calm to Buzzy", each
   * name under its picture. What the two are is said first to whoever hears the page, and is
   * read from the layout by whoever sees it.
   */
  between: "It runs from",
  to: "to",
  facts: {
    family: "Where to find it under Space requirements",
    word: "The everyday word for it",
  },
  /** In the fold of a vibe: the other names that were weighed for it, where any are set down. */
  names: {
    title: "Other names weighed for it",
  },
  /** The city coloured by the vibe. The name of the vibe and of each end are the API's. */
  map: {
    title: (vibe: string, low: string, high: string) =>
      `A map of the city coloured by ${vibe}, in five shades of green from ${low} to ${high}`,
    none: "There is no map of this vibe to show.",
    /** In place of the map of a vibe that no area can be placed on. It would be a map of dots. */
    notYet: "Burro cannot work this vibe out for any area yet, so there is no map of it to show.",
  },
  /** How much of what goes into a vibe Burro has, as one number, and how much an area needs. Both are the API's. */
  held: (held: number, needed: number) =>
    held === 0
      ? `Burro has none of these measurements yet, so it cannot work this vibe out for any area. It can do so once it has measurements that carry ${needed} of the 100 shares.`
      : held >= needed
        ? `Burro does not have all of these measurements yet. The ones it has carry ${held} of the 100 shares, which is enough to work the vibe out, so Burro works out every band from them alone.`
        : `Burro has only some of these measurements so far, and they carry ${held} of the 100 shares. It needs measurements that carry ${needed} of them, so it cannot work this vibe out for any area yet.`,
  whole: "Burro has every one of these measurements, so nothing is missing from this vibe.",
  /** The areas at each end of the vibe, by name, from the bands the API gives. */
  found: {
    title: "Where it is found",
    lead: "Burro sorts the areas into five bands, which the key draws as five steps. Band 5 holds the areas with the most of the vibe, or the ones nearest its second end.",
    /** Over the areas in the highest band and in the lowest. The name of an end is the API's. */
    end: (end: string) => `The areas at the ${end} end`,
    most: "The areas with the most of it",
    least: "The areas with the least of it",
    none: "No area",
    unplaced: "The areas Burro could not work it out for",
    /** In place of the names of an end, where there are too many to read: how many, and where they are named. */
    many: (count: number) => `${count} areas, which is too many to name here. Each of them is named below, band by band.`,
    /** What opens every area, band by band. */
    every: "Every area, band by band",
    band: (band: number) => `Band ${band}`,
  },
  recipe: {
    title: "What goes into it",
    lead: "Burro works this vibe out from the measurements below. The share of each one says how much it counts, and the shares add up to 100.",
    /** How much of the vibe a measurement carries, of the hundred its shares add up to. */
    share: (hundredths: number) => `${hundredths} of 100`,
    /** What the table is a table of. It is filled with the vibe's name. */
    caption: (vibe: string) => `What goes into ${vibe}`,
    columns: {
      part: "Measurement",
      reading: "How it counts",
      share: "Share",
      period: "Period",
      sources: "Source",
    },
    /** In place of the name of a measurement that Burro does not have, where the API names none. */
    notCarried: "A measurement Burro does not have yet",
    /** After the name of a measurement that Burro does not have. Its share still goes into the vibe. */
    waits: "Burro does not have it yet",
    noPeriod: "Burro does not have it yet",
    /** Under a measurement that goes into other vibes too. The names are the API's. */
    alsoIn: (vibes: string) => `It also goes into ${vibes}.`,
  },
  sources: "Where its measurements come from",
  noSources: "Burro has none of its measurements yet, so there is no source to show.",
  cannotSee: {
    title: "What it cannot see",
    lead: "No set of measurements can see everything. These are the things this vibe cannot tell you.",
  },
  methods: "Read how the ranking works, in the methods",
} as const;
