/**
 * Site copy for the page of vibes. It says how a vibe is worked out, in words
 * that stay true whatever release is loaded. Every vibe, its meaning, its
 * recipe, its sources and what it cannot see come from the API, so the page
 * can never disagree with the engine.
 *
 * The one number written here is a rule of the method that no route serves:
 * how much of a recipe an area must have a figure for. A test holds it to the
 * contract.
 */

export const VIBES = {
  title: "Vibes",
  lead: "A vibe is a published recipe over measured parts, and it says what it cannot see. A vibe that counts who lived in an area says so, and counts their age or their households and nothing else.",

  how: {
    title: "How an area is placed on a vibe",
    points: [
      "Each part of a recipe is read from its high end or its low end, and the parts are weighed by their shares. The shares of a recipe add up to 100.",
      "An area's band says where it sits among the areas compared, in fifths. Band 1 is the fifth nearest the low end, and band 5 the fifth nearest the high end. Areas that are level share a band.",
      "An area is placed only when it has a figure for parts that carry 60 of the 100 shares. With fewer, Burro says it cannot place the area, and never puts it in the middle.",
      "Where the homes of one area span three bands or more, the area is said to vary within itself, and is drawn as a range.",
      "A vibe is never shown as a percentage, a score or a rank. Five bands is as fine as its parts allow.",
      "The recipe is Burro's own, and the weights are a judgement. No language model writes or scores a vibe.",
    ],
  },

  contents: "The vibes of this data",
  /** Over the small maps at the head of the page: the same city, coloured by each vibe in turn. */
  glance: {
    lead: "The same city, coloured by each vibe in five bands. The darker an area, the nearer it is to the high end.",
    ends: (low: string, high: string) => `${low} to ${high}`,
  },
  scale: (low: string, high: string) => `A scale, counted from ${low} to ${high}.`,
  oneWay: "It runs one way, counted from least to most.",
  facts: {
    family: "In the settings under",
    word: "Everyday word",
  },
  /** Under the name of a vibe: the other names that were weighed for it, where any are set down. */
  names: {
    title: "Other names weighed for it",
  },
  /** The city coloured by the vibe. The name of the vibe and of each end are the API's. */
  map: {
    title: (vibe: string, low: string, high: string) =>
      `The areas of this data coloured by ${vibe}, in five bands from ${low} to ${high}`,
    /** Under the map: which way the colours run. */
    runs: (low: string, high: string) => `Lightest is ${low}, darkest is ${high}.`,
    notPlaced: "Dotted where Burro cannot place the area.",
    none: "This data has no map of this vibe.",
    /** In place of the map of a vibe that no area can be placed on. It would be a map of dots. */
    notYet: "No area can be placed on it yet, so there is no map of it.",
  },
  /** Beside a vibe at the head of the page that no area can be placed on. */
  notYet: "Not in this data yet",
  /** How much of a recipe the data holds, as one number, and how much an area needs. Both are the API's. */
  held: (held: number, needed: number) =>
    held === 0
      ? `This data holds none of its recipe. An area needs ${needed} of 100 to be placed.`
      : held >= needed
        ? `A band rests on ${held} of 100 of its recipe, which is what this data holds.`
        : `This data holds ${held} of 100 of its recipe. An area needs ${needed} of 100 to be placed.`,
  whole: "This data holds the whole of its recipe.",
  /** The areas at each end of the vibe, by name, from the bands the API gives. */
  found: {
    title: "Where it is found in this data",
    /** Over the areas in the highest band and in the lowest. The name of an end is the API's. */
    end: (end: string) => `At the ${end} end`,
    most: "Most",
    least: "Least",
    none: "No area of this data",
    unplaced: "Burro cannot place",
    /** In place of the names of an end, where there are too many to read: how many, and where they are named. */
    many: (count: number) => `${count} areas. Each is named below, band by band.`,
    /** What opens every area, band by band. */
    every: "Every area, band by band",
    band: (band: number) => `Band ${band}`,
  },
  /** What opens the period and the source of each part of the recipe. */
  detail: "The period and the source of each part",
  recipe: {
    title: "Recipe",
    /** In the short recipe: how much of the recipe a part carries, of the hundred it adds up to. */
    share: (hundredths: number) => `${hundredths} of 100`,
    /** What a table of a recipe is a table of. It is filled with the vibe's name. */
    caption: (vibe: string) => `What ${vibe} is made of`,
    columns: {
      part: "Part",
      reading: "How it is read",
      share: "Share of the recipe",
      period: "Period",
      sources: "Source",
    },
    shareOf: "of 100",
    /** In place of the name of a part that this data does not carry, where the API names none. */
    notCarried: "A part this data does not carry",
    /** After the name of a part that this data does not carry. Its share is still part of the recipe. */
    waits: "Not in this data yet",
    noPeriod: "Not in this data",
    /** Under a part that other recipes hold too. The names are the API's. */
    alsoIn: (vibes: string) => `Also a part of ${vibes}.`,
  },
  sources: "Sources",
  noSources: "No part of it is in this data.",
  cannotSee: "What it cannot see",
  methods: "How the ranking works, and what each part measures",
} as const;
