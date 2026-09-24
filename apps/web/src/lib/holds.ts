/**
 * What the release a page is built on can answer at all, read off route 11.
 *
 * A first build holds a few measures, a band for a few vibes, and no journey
 * and no cost. The page then says what is not there yet where a person would
 * look for it, and offers no control that the API could only turn away.
 * Nothing here is worked out: whether a vibe places any area, how much of
 * its recipe is held and what it waits on are the API's to say.
 */

import { EXAMPLE_POOL, EXAMPLES_SHOWN } from "@/content/search";
import type { MetaData, RecipeHeld, Tag, VibeBands } from "@/lib/api/schema";

type Form = Pick<MetaData, "recipes">;

/** What the release holds of one vibe's recipe. `undefined` where the API said nothing of it. */
export function recipeOf(form: Form, tagId: string): RecipeHeld | undefined {
  return form.recipes.find((held) => held.tag_id === tagId);
}

/**
 * Whether any area has a band for the vibe. A vibe the API says nothing of is
 * taken to be placed: the page then offers it, and the API answers for it.
 */
export function isPlaced(form: Form, tagId: string): boolean {
  return recipeOf(form, tagId)?.placed ?? true;
}

/** The vibes of the release that some area has a band for, in the order they came. */
export function placedOf<T extends Pick<Tag, "tag_id">>(form: Form, tags: readonly T[]): readonly T[] {
  return tags.filter((tag) => isPlaced(form, tag.tag_id));
}

/** The vibes of the release that no area has a band for, in the order they came. */
export function waitingOf<T extends Pick<Tag, "tag_id">>(form: Form, tags: readonly T[]): readonly T[] {
  return tags.filter((tag) => !isPlaced(form, tag.tag_id));
}

/**
 * What a sentence may ask for, as the target of a suggestion names it: `budget`,
 * `commute`, `feature:<id>` or `tag:<id>`. True where the release can answer it.
 */
export function canAnswer(form: Pick<MetaData, "recipes" | "holds" | "features">, target: string): boolean {
  if (target === "budget") return form.holds.costs;
  if (target === "commute") return form.holds.journeys;
  const [kind, id] = target.split(":", 2);
  if (kind === "tag" && id !== undefined) {
    return form.recipes.some((held) => held.tag_id === id && held.placed);
  }
  if (kind === "feature") return form.features.some((metric) => metric.feature_id === id && metric.rankable);
  return true;
}

/**
 * The sentences the first screen offers to start from: the first three that the release
 * can answer the whole of. An example the page itself suggests must give a list.
 */
export function examplesFor(form: Pick<MetaData, "recipes" | "holds" | "features">): readonly string[] {
  return EXAMPLE_POOL.filter((example) => example.asks.every((target) => canAnswer(form, target)))
    .slice(0, EXAMPLES_SHOWN)
    .map((example) => example.text);
}

/**
 * The bands of the vibes that some area is placed on. The bands of a vibe that places no
 * area are a thousand rows that each say nothing, and no map is coloured by them, so they
 * are not handed to the browser with the page.
 */
export function bandsToDraw(form: Form, bands: readonly VibeBands[]): readonly VibeBands[] {
  return bands.filter((one) => isPlaced(form, one.tag_id));
}
