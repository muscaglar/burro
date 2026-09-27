import { cleanup, render, screen, within } from "@testing-library/react";

import { STRIP } from "@/content/search";
import { TOWN } from "@/content/town";
import { recordedAnswer } from "@/lib/api/recorded";
import { isPlaced } from "@/lib/holds";
import { NOTHING_KNOWN, type Bands } from "@/lib/town/bands";
import { piecesOf, type Piece } from "@/lib/town/pieces";
import { planOf } from "@/lib/town/plan";
import { DRAWN_FROM, PARTS, type Part } from "@/lib/town/vibes";

import { faultsIn } from "../../../test/support/axe";
import { ROUGH, sayingSo } from "../../../test/support/rough";
import { TownKey } from "./TownKey";

const meta = recordedAnswer("get_meta", "meta").body.data;
/** A release that holds the recipe of one of the four, and too little of the other three. */
const preview = recordedAnswer("get_meta", "preview/meta").body.data;

const tagOf = (part: Part, of = meta) => of.tags.find((tag) => tag.tag_id === DRAWN_FROM[part]);
const rowOf = (container: HTMLElement, part: Part | "blank") => {
  const row = container.querySelector<HTMLElement>(`[data-part="${part}"]`);
  if (row === null) throw new Error("The key has no such row.");
  return row;
};
/** The towns of a row, each as the pieces it is drawn of. */
const townsIn = (row: HTMLElement) =>
  [...row.querySelectorAll<HTMLElement>("[data-size]")].map((town) =>
    [...town.children].map((piece) =>
      ["--art", "--frame", "--x", "--y"].map((name) => (piece as HTMLElement).style.getPropertyValue(name)).join(" "),
    ),
  );
const drawnAs = (pieces: readonly Piece[]) =>
  pieces.map(({ drawing, frame, left, top }) => `url("/art/${drawing}.png") ${frame} ${left} ${top}`);
const MIDDLE: Bands = { trees: 3, height: 3, lit: 3, roofs: 3 };

describe("the key of every town", () => {
  test("test_it_has_a_row_for_each_part_in_the_order_the_parts_are_said_in_and_one_for_what_is_blank", () => {
    const { container } = render(<TownKey meta={meta} />);

    expect([...container.querySelectorAll("[data-part]")].map((row) => row.getAttribute("data-part"))).toEqual([...PARTS, "blank"]);
    // It is a part of the key to the drawings, under a small heading of its own.
    expect(screen.getByRole("heading", { level: 3, name: TOWN.key.title })).toBeVisible();
    expect(screen.getByRole("region", { name: TOWN.key.title })).toBeVisible();
  });

  test("test_it_says_in_sight_that_a_town_is_a_drawing_based_on_four_vibes_and_is_not_a_picture_of_the_place", () => {
    render(<TownKey meta={meta} />);

    expect(screen.getByText(TOWN.key.lead)).toBeVisible();
    // As the founder wrote it, of every town: what it shows, and what it is not.
    expect(TOWN.key.lead).toContain(
      "Each little town is a drawing based on four of the area's vibes. This means it shows the character of the area, and is not a picture of what the place looks like.",
    );
    expect(TOWN.line).toContain("is not a picture of what the place looks like");
    expect(screen.getByText(TOWN.key.ends)).toBeVisible();
  });

  test("test_every_town_is_of_one_size_and_neither_end_is_said_to_be_the_better", () => {
    expect(TOWN.key.lead).toContain("Every town is the same size, and neither end of a vibe is the better one.");
    expect(/\b(best|worst|score|win|prize)\b/i.test(JSON.stringify(TOWN.key))).toBe(false);
  });

  test.each(PARTS)("test_each_part_names_its_vibe_and_its_two_ends_as_the_service_does: %s", (part) => {
    const { container } = render(<TownKey meta={meta} />);
    const row = rowOf(container, part);
    const tag = tagOf(part);

    expect(within(row).getByText(tag?.label ?? "")).toBeVisible();
    expect(within(row).getByText(TOWN.key.is[part])).toBeVisible();
    // A vibe that runs one way has the two ends every page gives it.
    expect(within(row).getByText(tag?.low_end ?? STRIP.least)).toBeVisible();
    expect(within(row).getByText(tag?.high_end ?? STRIP.most)).toBeVisible();
  });

  test.each(PARTS)("test_the_two_towns_of_a_part_are_drawn_by_the_rule_at_its_two_ends_with_the_rest_in_the_middle: %s", (part) => {
    const { container } = render(<TownKey meta={meta} />);

    expect(townsIn(rowOf(container, part))).toEqual([
      drawnAs(piecesOf(planOf({ ...MIDDLE, [part]: 1 }))),
      drawnAs(piecesOf(planOf({ ...MIDDLE, [part]: 5 }))),
    ]);
  });

  test("test_neither_end_is_marked_and_both_towns_are_of_one_size", () => {
    const { container } = render(<TownKey meta={meta} />);
    const towns = [...container.querySelectorAll<HTMLElement>("[data-size]")];

    expect(towns).toHaveLength(9);
    expect(new Set(towns.map((town) => `${town.style.getPropertyValue("--across")} ${town.style.getPropertyValue("--down")} ${town.dataset.size}`)).size).toBe(1);
    // A town of the key is for the eye: the name of its end is read, under it.
    expect(towns.filter((town) => town.getAttribute("aria-hidden") !== "true")).toEqual([]);
    expect(screen.queryAllByRole("img")).toEqual([]);
  });

  test("test_what_is_not_known_is_shown_blank_and_said_never_to_be_the_middle_nor_the_least", () => {
    const { container } = render(<TownKey meta={meta} />);
    const row = rowOf(container, "blank");

    expect(townsIn(row)).toEqual([drawnAs(piecesOf(planOf(NOTHING_KNOWN)))]);
    expect(within(row).getByText(TOWN.key.notKnown)).toBeVisible();
    expect(within(row).getByText(TOWN.key.blank)).toBeVisible();
    expect(TOWN.key.blank).toContain("It never draws the middle or the least in its place, because that would be a guess.");
  });

  test("test_each_row_is_a_row_of_the_key_with_its_two_towns_beside_what_is_said_of_them", () => {
    const { container } = render(<TownKey meta={meta} />);

    for (const part of PARTS) {
      const row = rowOf(container, part);
      expect([part, row.tagName, row.getAttribute("data-key"), row.getAttribute("data-drawn")]).toEqual([part, "LI", `built-of-${part}`, "wide"]);
      // What is said comes first for whoever hears the page, and the towns after it.
      expect([...row.children].map((one) => one.hasAttribute("data-says"))).toEqual([true, false]);
      expect(row.querySelectorAll("[data-drawn-here] [data-size]")).toHaveLength(2);
    }
  });

  test("test_it_may_be_laid_out_by_what_holds_it", () => {
    render(<TownKey meta={meta} className="of-the-key" />);

    expect(screen.getByRole("region", { name: TOWN.key.title })).toHaveClass("of-the-key");
  });
});

describe("the key of a release that cannot draw every part", () => {
  const held = PARTS.filter((part) => isPlaced(preview, DRAWN_FROM[part]));
  const waiting = PARTS.filter((part) => !held.includes(part));

  test("test_the_recorded_preview_places_areas_on_some_of_the_four_and_not_on_the_rest", () => {
    expect(held.length).toBeGreaterThan(0);
    expect(waiting.length).toBeGreaterThan(0);
  });

  test("test_a_part_no_area_can_be_placed_on_is_named_said_to_be_blank_in_every_town_and_draws_no_town", () => {
    const { container } = render(<TownKey meta={preview} />);

    for (const part of waiting) {
      const row = rowOf(container, part);
      expect(within(row).getByText(tagOf(part, preview)?.label ?? "")).toBeVisible();
      expect(within(row).getByText(TOWN.key.notYet)).toBeVisible();
      expect(townsIn(row)).toEqual([]);
    }
  });

  test("test_the_towns_of_a_part_that_can_be_drawn_leave_blank_what_the_release_leaves_blank", () => {
    const { container } = render(<TownKey meta={preview} />);
    const middle = Object.fromEntries(PARTS.map((part) => [part, held.includes(part) ? 3 : null])) as Bands;

    for (const part of held) {
      expect(townsIn(rowOf(container, part))).toEqual([
        drawnAs(piecesOf(planOf({ ...middle, [part]: 1 }))),
        drawnAs(piecesOf(planOf({ ...middle, [part]: 5 }))),
      ]);
    }
  });

  test("test_a_vibe_that_counts_recorded_crime_draws_no_town_in_the_key_and_says_why", () => {
    const crime = meta.features.find((one) => one.dimension === "crime");
    if (crime === undefined) throw new Error("The recorded release holds no measure of recorded crime.");
    const release = {
      ...meta,
      tags: meta.tags.map((tag) =>
        tag.tag_id === DRAWN_FROM.lit
          ? { ...tag, terms: [...tag.terms, { feature_id: crime.feature_id, hundredths: 10, reading: "high" as const }] }
          : tag,
      ),
    };
    const { container } = render(<TownKey meta={release} />);
    const row = rowOf(container, "lit");

    expect(within(row).getByText(TOWN.key.countsCrime)).toBeVisible();
    expect(townsIn(row)).toEqual([]);
    // And no town of any other row has a window lit.
    const lit = [...container.querySelectorAll<HTMLElement>("[data-size] > span")].filter(
      (piece) => /town-(low|mid|tall)/.test(piece.style.getPropertyValue("--art")) && piece.style.getPropertyValue("--frame") !== "0",
    );
    expect(lit).toEqual([]);
  });

  test("test_a_vibe_the_service_says_is_less_sure_is_named_in_the_key_as_every_vibe_is_and_nothing_is_said_of_it", () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a user".
    // No service calls a vibe a town is drawn from less sure. Here one does, and says so of
    // it in the words a service gave such a vibe until it stopped: its label, and why.
    const release = sayingSo(meta, [DRAWN_FROM.trees]);
    const { container } = render(<TownKey meta={release} />);
    const row = rowOf(container, "trees");

    expect(release.tags.find((tag) => tag.tag_id === DRAWN_FROM.trees)?.sureness).toBe("rough_guide");
    expect(release.rough_guides).toContainEqual({ ...ROUGH, tag_id: DRAWN_FROM.trees });
    expect(within(row).queryByText(ROUGH.label)).toBeNull();
    expect(within(row).queryByRole("note")).toBeNull();
    expect(container.querySelector("[data-rough-guide]")).toBeNull();
    expect([container.textContent?.includes(ROUGH.label), container.textContent?.includes(ROUGH.why)]).toEqual([false, false]);
    // Its row is the row of a release that says nothing of how sure the vibe is: its name, what it is, and a town at each end.
    expect(within(row).getByText(tagOf("trees")?.label ?? "")).toBeVisible();
    expect(townsIn(row)).toHaveLength(2);
    const said = row.textContent;
    cleanup();
    expect(rowOf(render(<TownKey meta={meta} />).container, "trees").textContent).toBe(said);
  });

  test("test_a_vibe_the_release_does_not_name_at_all_is_not_named_by_the_key", () => {
    const without = { ...meta, tags: meta.tags.filter((tag) => tag.tag_id !== DRAWN_FROM.roofs) };
    const { container } = render(<TownKey meta={without} />);
    const row = rowOf(container, "roofs");

    expect(within(row).getByText(TOWN.key.noVibe)).toBeVisible();
    expect(within(row).queryByText(tagOf("roofs")?.label ?? "")).toBeNull();
    expect(townsIn(row)).toEqual([]);
  });
});

describe("the accessibility of the key", () => {
  test.each([
    ["of a whole release", meta],
    ["of a preview", preview],
  ])("test_it_has_no_accessibility_fault: %s", async (_, of) => {
    const { container } = render(<TownKey meta={of} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
