import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { BAND_ON_A_SCALE, BAND_ONE_WAY, BAND_VARIES } from "@/content/bands";
import { CANNOT_PLACE } from "@/content/facts";
import { PEG } from "@/content/kit";

import { recordedAnswer } from "@/lib/api/recorded";

import { faultsIn } from "../../../../test/support/axe";
import { rulesOf } from "../../../../test/support/css";
import { sizeOf } from "../drawings";
import { picturesAtEnds } from "../Ends/picture";
import { Peg } from "./Peg";

const meta = recordedAnswer("get_meta", "meta").body.data;

const CSS = readFileSync(path.join(__dirname, "Peg.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const STYLES = rulesOf(CSS).filter((rule) => !/forced-colors/.test(rule.under ?? ""));
/** What the style sheet sets of a selector, each value on one line however it is written. */
const setsOf = (selector: string) =>
  new Map(
    STYLES.filter((rule) => rule.selector === selector).flatMap((rule) =>
      [...rule.sets].map(([property, value]): [string, string] => [property, value.replace(/\s+/g, " ")]),
    ),
  );
const BANDS = [1, 2, 3, 4, 5] as const;
const stepsOf = (container: HTMLElement) => [...container.querySelectorAll<HTMLElement>(".step")];
/** Which steps are marked, from the low end. */
const markedOf = (container: HTMLElement) => stepsOf(container).map((step) => step.dataset.here === "true");
/** Where the mark begins, in steps from the low end, and how many it lies across. */
const markOf = (container: HTMLElement) => {
  const steps = container.querySelector(".steps") as HTMLElement;
  return [steps.style.getPropertyValue("--at"), steps.style.getPropertyValue("--over")];
};

describe("where a place sits on a vibe", () => {
  test.each(BANDS)("test_it_says_its_band_in_words_beside_the_steps_and_in_the_name_of_the_picture: band %i", (band) => {
    render(<Peg band={band} />);

    expect(screen.getByRole("img")).toHaveAccessibleName(`band ${band} of 5, from least to most`);
    expect(screen.getByText(BAND_ONE_WAY[band])).toBeInTheDocument();
  });

  test.each(BANDS)("test_on_a_scale_it_says_which_end_by_the_names_the_api_gives_the_ends: band %i", (band) => {
    render(<Peg band={band} low="Calm" high="Buzzy" />);

    expect(screen.getByRole("img")).toHaveAccessibleName(`band ${band} of 5, from Calm to Buzzy`);
    expect(screen.getByText(BAND_ON_A_SCALE[band]("Calm", "Buzzy"))).toBeInTheDocument();
  });

  test.each(BANDS)("test_it_is_five_steps_with_a_peg_on_one_and_never_a_bar_that_fills: band %i", (band) => {
    const { container } = render(<Peg band={band} />);

    expect(stepsOf(container)).toHaveLength(5);
    // One step is marked, which is the step of its band: and not every step as far as that one.
    expect(markedOf(container)).toEqual(BANDS.map((one) => one === band));
    expect(markOf(container)).toEqual([String(band - 1), "1"]);
    expect(container.querySelectorAll(".mark")).toHaveLength(1);
    expect(container.querySelector(".rail")).toBeNull();
  });

  test("test_the_peg_is_the_drawing_of_a_peg_and_stands_in_the_middle_of_its_step", () => {
    const { container } = render(<Peg band={2} />);
    const steps = container.querySelector(".steps") as HTMLElement;
    const { width, height } = sizeOf("ui-peg");
    const mark = setsOf(".mark");

    expect(steps.style.getPropertyValue("--art")).toBe('url("/art/ui-peg.png")');
    expect([steps.style.getPropertyValue("--w"), steps.style.getPropertyValue("--h")]).toEqual([String(width), String(height)]);
    // A step is nine art pixels wide and the steps stand one apart: so the next step is ten
    // further along. Inside its rule a step is seven wide, and begins two in from the left.
    expect(setsOf(".steps").get("grid-template-columns")).toBe("repeat(5, calc(var(--px) * 9))");
    expect(setsOf(".steps").get("gap")).toBe("var(--px)");
    expect(mark.get("inset-inline-start")).toBe("calc(var(--px) * (2 + 10 * var(--at) + (7 - var(--w)) / 2))");
    expect(width).toBeLessThanOrEqual(7);
    expect((7 - width) % 2).toBe(0);
    // It is shown at its own size, with a hard edge, and is never stretched.
    expect(mark.get("background")).toBe("var(--art) 0 0 / calc(var(--px) * var(--w)) calc(var(--px) * var(--h)) no-repeat");
    expect(mark.get("image-rendering")).toBe("pixelated");
  });

  test("test_the_room_of_the_peg_is_there_whether_a_peg_is_or_not", () => {
    // A line with a peg and a line with none are of one height: nothing moves as one gives way to the other.
    expect(setsOf(".steps").get("padding")).toBe("calc(var(--px) * (var(--h) - 3)) var(--px) 0");
    expect(setsOf(".mark").get("position")).toBe("absolute");
    expect(setsOf(".rail").get("position")).toBe("absolute");
    // A state changes what a step is filled with, and nothing else of it: not its edge, and not the room it takes.
    const states = STYLES.filter((rule) => /\[data-(placed|mixed|part|asked|here)/.test(rule.selector));
    expect(states.length).toBeGreaterThan(2);
    expect([...new Set(states.flatMap((rule) => [...rule.sets.keys()]))].sort()).toEqual(["background"]);
  });

  test("test_the_ends_of_a_scale_are_named_under_its_steps_and_said_once_by_the_picture", () => {
    render(<Peg band={2} low="Newer" high="Historic" />);
    const picture = screen.getByRole("img");

    // They stand inside the picture, which says them in its name: none is heard a second time.
    expect(within(picture).getByText("Newer")).toBeInTheDocument();
    expect(within(picture).getByText("Historic")).toBeInTheDocument();
    expect(screen.getAllByText("Newer")).toHaveLength(1);
  });

  test("test_the_ends_of_a_vibe_that_runs_one_way_are_said_by_the_picture_and_not_drawn", () => {
    const { container } = render(<Peg band={2} />);

    expect(container.querySelector(".ends")).toBeNull();
    expect(screen.getByRole("img")).toHaveAccessibleName("band 2 of 5, from least to most");
  });

  test("test_each_end_may_be_drawn_with_its_small_picture_and_is_then_named_once", () => {
    const { container } = render(<Peg band={4} low="Houses" high="Flats" pictured />);
    const pictures = [...container.querySelectorAll<HTMLElement>(".art")].map((one) => one.style.getPropertyValue("--art"));

    expect(pictures).toEqual(['url("/art/key-houses.png")', 'url("/art/key-flats.png")']);
    expect(screen.getAllByText("Houses")).toHaveLength(1);
    expect(screen.getAllByText("Flats")).toHaveLength(1);
    // The steps run between the two.
    expect(container.querySelector(".between .steps")).not.toBeNull();
    expect(screen.getByRole("img")).toHaveAccessibleName("band 4 of 5, from Houses to Flats");
  });

  test("test_handed_the_id_of_its_vibe_each_end_has_the_one_picture_of_that_end_of_that_vibe_whichever_way_the_vibe_runs", () => {
    // A picture stands at each end of every gauge, and the two are opposites. By the name
    // of an end every vibe that runs one way had the same two, of homes and of trees.
    for (const tag of meta.tags) {
      const { container, unmount } = render(<Peg band={3} low={tag.low_end} high={tag.high_end} pictured id={tag.tag_id} />);
      const pictures = [...container.querySelectorAll<HTMLElement>(".art")].map((one) => one.style.getPropertyValue("--art"));

      expect([tag.tag_id, pictures]).toEqual([tag.tag_id, picturesAtEnds(tag.tag_id).map((name) => `url("/art/${name}.png")`)]);
      expect([tag.tag_id, new Set(pictures).size]).toEqual([tag.tag_id, 2]);
      // The steps run between the two, and the picture says the band and both ends as it did.
      expect(container.querySelector(".between .steps")).not.toBeNull();
      const [low, high] = [tag.low_end ?? "least", tag.high_end ?? "most"];
      expect(screen.getByRole("img")).toHaveAccessibleName(`band 3 of 5, from ${low} to ${high}`);
      unmount();
    }
    expect(meta.tags.some((tag) => tag.low_end === null)).toBe(true);
    // Handed no id, an end is drawn by its name, as it was.
    const { container } = render(<Peg band={4} low="Houses" high="Flats" pictured />);
    expect([...container.querySelectorAll<HTMLElement>(".art")].map((one) => one.style.getPropertyValue("--art"))).toEqual([
      'url("/art/key-houses.png")',
      'url("/art/key-flats.png")',
    ]);
    // No id is written into the part: it is handed one, which the service gave.
    const written = readFileSync(path.join(__dirname, "Peg.tsx"), "utf8");
    expect(meta.tags.filter((tag) => written.includes(`"${tag.tag_id}"`))).toEqual([]);
  });

  test("test_a_vibe_that_was_asked_for_says_so_in_the_picture_and_for_the_eye", () => {
    const { container } = render(<Peg band={4} asked />);

    expect(screen.getByRole("img")).toHaveAccessibleName("band 4 of 5, from least to most, asked for");
    expect(screen.getByText("asked for")).toHaveAttribute("aria-hidden", "true");
    expect(container.firstElementChild).toHaveAttribute("data-asked", "true");
  });

  test("test_on_a_scale_it_says_which_end_was_asked_for", () => {
    const { rerender } = render(<Peg band={4} low="Calm" high="Buzzy" asked="high" />);
    expect(screen.getByRole("img")).toHaveAccessibleName("band 4 of 5, from Calm to Buzzy, asked for: Buzzy");

    rerender(<Peg band={4} low="Calm" high="Buzzy" asked="low" />);
    expect(screen.getByRole("img")).toHaveAccessibleName("band 4 of 5, from Calm to Buzzy, asked for: Calm");
  });

  test("test_a_vibe_that_was_not_asked_for_says_nothing_of_it", () => {
    const { container } = render(<Peg band={4} />);

    expect(screen.queryByText("asked for")).toBeNull();
    expect(container.firstElementChild).toHaveAttribute("data-asked", "false");
  });

  test("test_a_band_that_rests_on_part_of_its_recipe_has_its_step_chequered_and_says_so_in_the_line_it_is_given", () => {
    const { container } = render(<Peg band={2} part="Worked out from 3 of its 5 parts, 70 of 100 by weight." />);

    expect(screen.getByText("Worked out from 3 of its 5 parts, 70 of 100 by weight.")).toBeInTheDocument();
    expect(container.firstElementChild).toHaveAttribute("data-part", "true");
    // The peg stands as it would: it is the step under it that is chequered.
    expect(markedOf(container)).toEqual([false, true, false, false, false]);
    expect(container.querySelectorAll(".mark")).toHaveLength(1);
    expect(setsOf('.peg[data-part="true"] .step[data-here="true"]').get("background")).toBe(
      "repeating-conic-gradient(var(--ink) 0 25%, var(--page) 0 50%) 0 0 / calc(var(--px) * 4) calc(var(--px) * 4)",
    );
    // The line is the API's or the website's own. The peg writes none, and adds up nothing.
    render(<Peg band={2} part="from 3 of its 5 parts" />);
    expect(screen.getAllByText("from 3 of its 5 parts")).toHaveLength(1);
  });

  test("test_a_mixed_place_has_a_rail_that_joins_the_steps_it_spans_and_no_peg", () => {
    const { container } = render(<Peg band={3} spread={[2, 4]} low="Newer" high="Historic" />);

    // Never a point in the middle: there is no peg at all.
    expect(container.querySelector(".mark")).toBeNull();
    expect(container.querySelectorAll(".rail")).toHaveLength(1);
    expect(markOf(container)).toEqual(["1", "3"]);
    expect(markedOf(container)).toEqual([false, true, true, true, false]);
    expect(container.firstElementChild).toHaveAttribute("data-mixed", "true");
    expect(screen.getByRole("img")).toHaveAccessibleName(
      "varies within this area, between band 2 and band 4 of 5, from Newer to Historic",
    );
    expect(screen.getByText(BAND_VARIES)).toBeInTheDocument();
    // The steps it spans are sand, and the rail lies over them, from the first to the last.
    expect(setsOf('.peg[data-mixed="true"] .step[data-here="true"]').get("background")).toBe("var(--sand)");
    expect(setsOf(".rail").get("inset-inline-start")).toBe("calc(var(--px) * 10 * var(--at))");
    expect(setsOf(".rail").get("width")).toBe("calc(var(--px) * (10 * var(--over) + 1))");
  });

  test("test_a_place_that_spans_two_bands_is_drawn_in_the_one_it_sits_in", () => {
    const { container } = render(<Peg band={3} spread={[3, 4]} />);

    expect(container.querySelector(".rail")).toBeNull();
    expect(markOf(container)).toEqual(["2", "1"]);
    expect(markedOf(container)).toEqual([false, false, true, false, false]);
  });

  test("test_a_place_that_cannot_be_placed_has_five_empty_steps_and_no_peg_never_the_middle_and_never_nought", () => {
    const { container } = render(<Peg band={null} low="Polished" high="Gritty" />);

    // The picture is named for what is drawn, as the key to the drawings names it, and says
    // nothing of how a band is counted: there is no band to count. What it means stands in
    // words beside the steps, and is heard once.
    expect(screen.getByRole("img")).toHaveAccessibleName(PEG.empty);
    expect(PEG.empty).toBe("Five empty steps, with no peg");
    expect(screen.getAllByText(CANNOT_PLACE)).toHaveLength(1);
    expect(screen.getByRole("img")).not.toHaveTextContent(CANNOT_PLACE);
    // Nothing stands on the steps, and no step is marked: not the middle one, and not the first.
    expect(stepsOf(container)).toHaveLength(5);
    expect(stepsOf(container).filter((step) => step.hasAttribute("data-here"))).toEqual([]);
    expect(container.querySelector(".mark, .rail")).toBeNull();
    expect(container.firstElementChild).toHaveAttribute("data-placed", "false");
    // Each step has the whole edge of any step, and holds nothing. They were drawn in dashes,
    // which a person who walked the website did not understand: what cannot be placed is
    // told by there being no step of ink and no peg, and by the words beside the steps.
    expect(STYLES.filter((rule) => /data-placed/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
    expect([setsOf(".step").get("border"), setsOf(".step").get("background")]).toEqual(["var(--px) solid var(--ink)", "var(--page)"]);
    expect(/dashed|dotted|border-box/.test(CSS)).toBe(false);
  });

  test("test_a_place_that_cannot_be_placed_is_drawn_one_way_by_the_kit_and_by_the_line_of_a_vibe_and_whole", () => {
    // The key to the drawings draws the state with this part, and a result and the page of
    // an area draw it with the line of a vibe. Seen in a browser: the key drew five pairs
    // of brackets, each step an edge with its middle taken out, where every page drew five
    // whole steps. It was drawn with gradients laid over a clear edge, so no search for
    // "dashed" found it. One state is drawn one way.
    const line = rulesOf(readFileSync(path.join(__dirname, "../../Track/Track.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "")).filter(
      (rule) => !/forced-colors/.test(rule.under ?? ""),
    );
    const cell = new Map(line.filter((rule) => rule.selector === ".cell").flatMap((rule) => [...rule.sets]));

    expect([cell.get("border"), cell.get("background")]).toEqual([setsOf(".step").get("border"), setsOf(".step").get("background")]);
    for (const [sheet, step, marked] of [
      [STYLES, ".step", '[data-here="true"]'],
      [line, ".cell", '[data-on="true"]'],
    ] as const) {
      const ofAStep = sheet.filter((rule) => rule.selector.includes(step));
      // Neither sheet knows the state: a step of it is a step at rest.
      expect(ofAStep.filter((rule) => /data-placed/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
      // Nothing is laid on a step at rest, and its edge is never taken off it or made clear.
      const laid = ofAStep.filter((rule) => [...rule.sets.values()].some((value) => /gradient\(/.test(value)));
      expect(laid.filter((rule) => !rule.selector.includes(marked)).map((rule) => rule.selector)).toEqual([]);
      const edges = ofAStep.flatMap((rule) => [...rule.sets].filter(([property]) => /^border/.test(property)).map(([, value]) => value));
      expect(edges.filter((value) => /transparent|none|\b0\b/.test(value))).toEqual([]);
    }
  });

  test("test_a_band_the_website_has_no_word_for_is_said_by_the_picture_and_no_word_is_made_up", () => {
    const { container } = render(<Peg band={6} />);

    expect(screen.getByRole("img")).toHaveAccessibleName("band 6 of 5, from least to most");
    expect(container.querySelector(".words")).toBeNull();
  });

  test("test_what_it_says_is_read_and_is_set_in_the_reading_face", () => {
    expect(setsOf(".peg").get("font")).toBe("400 var(--size-body) / 1.3 var(--font-say)");
    expect(STYLES.filter((rule) => [...rule.sets.values()].some((value) => /var\(--font-name\)/.test(value)))).toEqual([]);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <ul>
        <li>
          <Peg band={1} />
        </li>
        <li>
          <Peg band={4} low="Calm" high="Buzzy" asked="high" />
        </li>
        <li>
          <Peg band={4} low="Houses" high="Flats" pictured />
        </li>
        <li>
          <Peg band={2} part="from 3 of its 5 parts" />
        </li>
        <li>
          <Peg band={3} spread={[2, 4]} />
        </li>
        <li>
          <Peg band={null} />
        </li>
      </ul>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
