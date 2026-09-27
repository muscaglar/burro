/**
 * What a service said of a vibe it called a rough guide, until it stopped, for a test to
 * lay on an answer that was recorded since.
 *
 * The founder walked the website and wrote: "remove the concept of rough guide, we don't
 * want to pass this on to a user". The website stopped drawing the label and the sentence
 * that said why. On 2026-09-26 the service stopped saying them: `rough_guides` of route 11
 * is a list that is always empty, and no offer says either in its note. Which vibe is less
 * sure it says still, in `sureness` of the vibe, which is a code and no words.
 *
 * So no recorded answer holds the words, and a test that took them from one would hold
 * nothing of a page. It is the website that is tested, and a service that is older than
 * it, or later, may send them. A test that holds that no page says them lays them on a
 * recorded answer first, from here. They are written in this file and in no other.
 */

import { readdirSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedFolder, type Recorded } from "@/lib/api/recorded";
import type { InterpretData, MetaData, RoughGuide, TagId } from "@/lib/api/schema";

/**
 * The vibe it was said of, the label, and the sentence that said why: word for word as
 * route 11 gave them, in `rough_guides`, in the last answers that were recorded with them.
 */
export const ROUGH: RoughGuide = {
  tag_id: "village_feel",
  label: "Rough guide",
  why: "This vibe is less sure than the others, because only about half of the areas it puts highest seemed like villages to the people who were asked, and it also takes some busy main roads and some grand streets near the centre of the city for villages.",
};

/** What stood in the note of an offer of the vibe, after whatever else the note held: the label, and then the sentence. */
export const ROUGH_NOTE = `${ROUGH.label}. ${ROUGH.why}`;

/**
 * What says that a vibe is a rough guide, however it is written: the label, and what opens
 * and what closes the sentence. The service holds its own answers to the same three.
 */
export const SAYS_SO = /rough guide|less sure|seemed like villages/i;

/** The vibes an answer of route 11 calls less sure, in its code. */
const lessSureIn = (tags: MetaData["tags"]) => tags.filter((tag) => tag.sureness === "rough_guide");

/**
 * An answer of route 11 as a service that said so gave it: the answer as it was recorded,
 * and in `rough_guides` the label and the sentence of each vibe its code calls less sure.
 *
 * Which vibe is less sure is the recorded service's to say, and is laid by nothing here. An
 * answer whose code does not say it of the vibe is refused: so a test that lays the words
 * holds that the code is served still, and none passes because nothing was laid.
 *
 * `also` names other vibes, for a test that holds that whatever is said of whichever vibe,
 * no page says it. No service was recorded saying it of them, so each is given the code
 * here, with the label and the sentence.
 */
export function sayingSo(meta: MetaData, also: readonly TagId[] = []): MetaData {
  if (!lessSureIn(meta.tags).some((tag) => tag.tag_id === ROUGH.tag_id)) {
    throw new Error("The answer does not say in its code which vibe is less sure, so nothing a service said of one can be laid on it.");
  }
  const tags =
    also.length === 0
      ? meta.tags
      : meta.tags.map((tag) => (also.includes(tag.tag_id) ? { ...tag, sureness: "rough_guide" as const } : tag));
  return { ...meta, tags, rough_guides: lessSureIn(tags).map((tag) => ({ ...ROUGH, tag_id: tag.tag_id })) };
}

/**
 * An answer of route 1 as such a service gave it: the reading as it was recorded, and in
 * the note of each offer of the vibe the label and the sentence, after whatever the note
 * held. A reading that offers no such vibe is refused, as nothing would be laid on it.
 */
export function offeringSo(read: InterpretData): InterpretData {
  const ofTheVibe = `tag:${ROUGH.tag_id}`;
  if (!read.suggestions.some((offer) => offer.target === ofTheVibe)) {
    throw new Error("The reading offers no vibe that a service called a rough guide, so nothing it said of one can be laid on it.");
  }
  return {
    ...read,
    suggestions: read.suggestions.map((offer) =>
      offer.target === ofTheVibe ? { ...offer, note: [offer.note, ROUGH_NOTE].filter((words) => words !== "").join(" ") } : offer,
    ),
  };
}

/**
 * Whether the service that a page reads as it is built says so. As it was recorded it
 * does not. A test of a whole page turns this on before the page is built, and it is off
 * again when the test ends.
 */
export const service = { saysSo: false };

if (typeof afterEach === "function") {
  afterEach(() => {
    service.saysSo = false;
  });
}

type Server = typeof import("@/lib/api/server");

/**
 * What reads the service as a page is built, for a test of a whole page to put in its
 * place: it reads route 11 as it was recorded, and lays on it what a service said while
 * `service.saysSo` is on. A page draws what it reads there, so nothing else can hand it a
 * release that says so. Every other route is read as it was.
 *
 *     jest.mock("@/lib/api/server", () =>
 *       jest.requireActual<typeof import("./support/rough")>("./support/rough").asAPageReads(jest.requireActual("@/lib/api/server")),
 *     );
 */
export function asAPageReads(server: Server): Server {
  return {
    ...server,
    loadMeta: async () => {
      const read = await server.loadMeta();
      return service.saysSo ? { ...read, data: sayingSo(read.data) } : read;
    },
  };
}

/** The names of the scenarios that were recorded, under a folder. */
function scenarios(folder = recordedFolder(), prefix = ""): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    if (entry.isDirectory()) return scenarios(path.join(folder, entry.name), `${prefix}${entry.name}/`);
    if (!entry.name.endsWith(".json") || entry.name === "index.json") return [];
    return [`${prefix}${entry.name.slice(0, -".json".length)}`];
  });
}

/** Every answer that was recorded, as it was recorded. */
export function everyRecording(): readonly Recorded[] {
  return scenarios().sort().map(readRecorded);
}

/**
 * How the caution on recorded rents ended until 2026-09-27, and how it ends since, word
 * for word. It was said of rents and of no vibe, and a page shows the caution as it comes:
 * so they were the last words of the service that a page could say so in.
 */
export const OF_RENTS = {
  said: "Burro uses them as a rough guide to what a home lets for.",
  says: "Burro uses them to give a general idea of what a home lets for.",
};

/**
 * Of some answers, those in which a service says something of a rough guide, by the name
 * of each scenario: anything at all in `rough_guides`, or a word that says so in any
 * string of what it sent. Of the answers as they are recorded a test expects none.
 *
 * Nothing is set aside. While the caution on rents said so it was, wherever the answer of
 * route 11 that gave it stood among the answers: a service that said so of rents again
 * would be found, as the service's own tests would find it. What a scenario is there to
 * show is written by the recorder and is no word of the service, so it is not read.
 */
export function sayingSoAmong(recordings: readonly Recorded[]): string[] {
  return recordings
    .filter(({ body }) => {
      const sent = JSON.stringify(body) ?? "";
      return /"rough_guides":\[(?!\])/.test(sent) || SAYS_SO.test(sent);
    })
    .map(({ scenario }) => scenario);
}
