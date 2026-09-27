import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { CHIPS } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { ChipKind } from "@/lib/search/chips";

import { faultsIn } from "../../../../test/support/axe";
import { rulesOf } from "../../../../test/support/css";
import { isDrawn, sizeOf } from "../drawings";
import { drawingOf, outlineOf, PLAIN, THING_KINDS, THING_STATES, type ThingKind } from "./drawn";
import { saidOf, Thing } from "./Thing";

const meta = recordedAnswer("get_meta", "meta").body.data;
const CSS = readFileSync(path.join(__dirname, "Thing.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const STYLES = rulesOf(CSS);

/** The picture that is drawn, as the page names it. */
const pictureIn = (container: HTMLElement) =>
  (container.querySelector(".drawing") as HTMLElement | null)?.style.getPropertyValue("--art") ?? null;

describe("the small drawing that stands for a thing of a search", () => {
  test("test_it_draws_the_picture_named_for_the_id_it_is_given", () => {
    const { container } = render(<Thing kind="tag" id="leafy" family="green" />);

    expect(pictureIn(container)).toBe('url("/art/thing-leafy.png")');
  });

  test("test_every_vibe_and_every_measure_of_the_recorded_release_is_drawn_and_none_by_nothing", () => {
    const vibes = meta.tags.map((tag) => drawingOf({ kind: "tag", id: tag.tag_id, family: tag.family }));
    const measures = meta.features.map((one) => drawingOf({ kind: "feature", id: one.feature_id, family: one.family }));

    expect(vibes.length).toBeGreaterThan(10);
    expect(measures.length).toBeGreaterThan(50);
    expect([...vibes, ...measures].filter((drawing) => !isDrawn(drawing))).toEqual([]);
  });

  test("test_every_vibe_of_the_recorded_release_is_drawn_by_a_drawing_of_its_own_today", () => {
    // The small drawing of a vibe stands with its name and with its gauge. A later release
    // may bring a vibe that nobody has drawn, and its family's drawing stands for it: every
    // vibe there is today has its own, whatever its id begins with.
    const ofFamilies = new Set(meta.families.map(({ family }) => drawingOf({ kind: "feature", family })));
    const vibes = meta.tags.map((tag) => [tag.tag_id, drawingOf({ kind: "tag", id: tag.tag_id, family: tag.family })] as const);

    expect(vibes.filter(([, drawing]) => ofFamilies.has(drawing) || drawing === PLAIN).map(([id]) => id)).toEqual([]);
    expect(new Set(vibes.map(([, drawing]) => drawing)).size).toBe(vibes.length);
  });

  test("test_every_group_of_measures_that_stands_apart_is_drawn_and_none_by_the_plain_box", () => {
    // The brands nearby, air and noise, and recorded crime stood under the plain box. Each
    // is drawn by the dimension the service gives its measures, handed on as a family is.
    const apart = [...new Set(meta.features.filter((one) => one.family === null || one.dimension === "brands").map((one) => one.dimension))];
    const drawn = apart.map((dimension) => drawingOf({ kind: "feature", family: dimension }));

    expect(apart).toHaveLength(3);
    expect(drawn.filter((drawing) => drawing === PLAIN)).toEqual([]);
    expect(new Set(drawn).size).toBe(apart.length);
    expect(drawn.filter((drawing) => outlineOf(drawing) === null)).toEqual([]);
  });

  test("test_a_thing_of_any_kind_in_any_state_is_never_drawn_as_nothing", () => {
    for (const kind of THING_KINDS) {
      for (const state of THING_STATES) {
        const { container, unmount } = render(<Thing kind={kind} id="of_a_later_release" family={null} state={state} />);

        expect([kind, state, /^url\("\/art\/[a-z0-9-]+\.png"\)$/.test(pictureIn(container) ?? "")]).toEqual([kind, state, true]);
        unmount();
      }
    }
    expect(isDrawn(PLAIN)).toBe(true);
  });

  test("test_every_kind_of_chip_is_a_kind_of_thing_by_the_same_name", () => {
    // A chip is drawn as a thing by handing its kind on. This is held by the types: a kind
    // of chip that is no kind of thing does not compile.
    const chips: readonly ChipKind[] = ["tenure", "budget", "place", "feature", "tag", "area"];
    const things: readonly ThingKind[] = chips;

    expect(things.every((kind) => THING_KINDS.includes(kind))).toBe(true);
  });

  test("test_it_is_shown_at_its_own_size_with_a_hard_edge_and_is_never_stretched", () => {
    const { container } = render(<Thing kind="budget" />);
    const drawn = container.querySelector(".drawing") as HTMLElement;
    const { width, height } = sizeOf("thing-budget");
    const [drawing] = STYLES.filter((rule) => rule.selector === ".drawing");

    expect([drawn.style.getPropertyValue("--w"), drawn.style.getPropertyValue("--h")]).toEqual([String(width), String(height)]);
    expect(drawing?.sets.get("background")).toBe(
      "var(--art) 0 0 / calc(var(--px) * var(--w)) calc(var(--px) * var(--h)) no-repeat",
    );
    expect(drawing?.sets.get("image-rendering")).toBe("pixelated");
  });

  test("test_with_words_it_is_a_picture_that_says_what_it_holds_and_then_its_state", () => {
    const { rerender } = render(<Thing kind="tag" id="leafy" family="green" says="Leafy: more" />);
    expect(screen.getByRole("img")).toHaveAccessibleName("Leafy: more");

    rerender(<Thing kind="tag" id="leafy" family="green" says="Leafy: more" state="assumed" />);
    expect(screen.getByRole("img")).toHaveAccessibleName(`Leafy: more, ${CHIPS.assumed}`);

    rerender(<Thing kind="tag" id="leafy" family="green" says="Leafy: more" state="off" />);
    expect(screen.getByRole("img")).toHaveAccessibleName(`Leafy: more, ${CHIPS.off}`);
  });

  test("test_the_words_for_a_state_are_the_ones_the_website_has", () => {
    expect([CHIPS.assumed, CHIPS.off]).toEqual(["assumed", "does not count"]);
    expect(saidOf("Quiet streets: more", "off")).toBe("Quiet streets: more, does not count");
    expect(saidOf("Quiet streets: more", "said")).toBe("Quiet streets: more");
  });

  test("test_with_no_words_it_stands_beside_them_and_is_kept_from_a_screen_reader", () => {
    const { container } = render(<Thing kind="budget" state="off" />);

    expect(screen.queryByRole("img")).toBeNull();
    expect(container.firstElementChild).toHaveAttribute("aria-hidden", "true");
  });

  test("test_what_counts_for_nothing_is_drawn_in_outline_by_the_drawing_of_its_outline", () => {
    const { container } = render(<Thing kind="tag" id="leafy" family="green" state="off" />);

    // It is in the search still, and is as large as it was: its colour is taken off it.
    expect(pictureIn(container)).toBe('url("/art/thing-leafy-off.png")');
    expect(container.querySelector(".thing")).toHaveAttribute("data-state", "off");
    expect(container.querySelector(".drawing")).toHaveAttribute("data-cut", "false");
    expect(sizeOf("thing-leafy-off")).toEqual(sizeOf("thing-leafy"));
    // Nothing is dimmed to say it: no rule of the style sheet fades a thing or sees through it.
    expect(/opacity|filter/.test(CSS)).toBe(false);
  });

  test("test_every_thing_of_the_recorded_release_has_an_outline_to_be_drawn_in", () => {
    const things = [
      ...meta.tags.map((tag) => drawingOf({ kind: "tag", id: tag.tag_id, family: tag.family })),
      ...meta.features.map((one) => drawingOf({ kind: "feature", id: one.feature_id, family: one.family })),
      ...THING_KINDS.filter((kind) => kind !== "tag" && kind !== "feature").map((kind) => drawingOf({ kind })),
    ];

    expect([...new Set(things)].filter((drawing) => outlineOf(drawing) === null)).toEqual([]);
  });

  test("test_a_thing_with_no_drawing_of_its_outline_has_it_cut_from_its_own_drawing", () => {
    const [cut] = STYLES.filter((rule) => rule.selector === '.drawing[data-cut="true"]');

    // The drawing is what cuts the shape out, and one flat colour is what is seen through it.
    expect(cut?.sets.get("background")).toBe("var(--shade)");
    expect((cut?.sets.get("mask-image") ?? "").split("var(--art)").length - 1).toBe(5);
    expect(cut?.sets.get("mask-size")).toBe("calc(var(--px) * var(--w)) calc(var(--px) * var(--h))");
    // Nothing of the outline changes the room the thing takes.
    expect([...(cut?.sets.keys() ?? [])].filter((property) => /^(width|height|margin|padding|display|position|inset)/.test(property))).toEqual([]);
  });

  test("test_what_a_person_said_has_no_mark_and_what_nobody_said_has_a_solid_edge_of_ink", () => {
    const { container, rerender } = render(<Thing kind="usual" />);
    expect(container.querySelector(".thing")).toHaveAttribute("data-state", "said");
    expect(container.querySelector(".thing")?.children).toHaveLength(1);

    rerender(<Thing kind="usual" state="assumed" />);
    const edge = STYLES.filter((rule) => /\[data-state="assumed"\]/.test(rule.selector) && rule.under === null);
    expect(container.querySelector(".thing")).toHaveAttribute("data-state", "assumed");
    expect(edge.map((rule) => [rule.selector, rule.sets.get("outline")])).toEqual([
      ['.thing[data-state="assumed"][data-edged="true"]', "var(--px) solid var(--ink)"],
    ]);
    // The edge is drawn round it, and takes no room of its own.
    expect(edge.flatMap((rule) => [...rule.sets.keys()]).sort()).toEqual(["outline", "outline-offset"]);
    // It is never the edge alone that says it: the name of the picture says "assumed", or the words beside it do.
    rerender(<Thing kind="usual" state="assumed" says="Renting" />);
    expect(screen.getByRole("img")).toHaveAccessibleName(`Renting, ${CHIPS.assumed}`);
  });

  test("test_no_edge_of_a_thing_is_drawn_in_dashes_or_in_dots", () => {
    // A person who walked the website did not know what a dashed edge was for.
    expect(/dashed|dotted|repeating-linear-gradient/.test(CSS)).toBe(false);
    expect(STYLES.filter((rule) => /^(border|outline)-style$/.test([...rule.sets.keys()].join(" "))).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <p>
        {THING_STATES.map((state) => (
          <Thing key={state} kind="tag" id="leafy" family="green" state={state} says="Leafy: more" />
        ))}
        <Thing kind="feature" id="crime_burglary_theft" family={null} says="Recorded burglary and theft" />
        <Thing kind="place" />
      </p>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
