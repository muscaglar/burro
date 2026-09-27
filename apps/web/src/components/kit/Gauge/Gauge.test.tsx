import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { SLIDER } from "@/content/settings";

import { faultsIn } from "../../../../test/support/axe";
import { rulesOf } from "../../../../test/support/css";
import { sizeOf } from "../drawings";
import { filledOf, STEPS, within } from "./filled";
import { Gauge, inWords } from "./Gauge";

const CSS = readFileSync(path.join(__dirname, "Gauge.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const STYLES = rulesOf(CSS).filter((rule) => !/forced-colors/.test(rule.under ?? ""));
const PEG = readFileSync(path.join(__dirname, "..", "Peg", "Peg.tsx"), "utf8");

const cellsOf = (container: HTMLElement) => [...container.querySelectorAll<HTMLElement>(".cell")];
const markOf = (container: HTMLElement) => container.querySelector(".mark") as HTMLElement;
const leftOf = (drawn: HTMLElement) => Number(drawn.style.getPropertyValue("--left"));
const CELL = sizeOf("gauge-cell");
const MARK = sizeOf("ui-weight");

describe("how much a thing counts", () => {
  test("test_alone_it_says_how_much_in_words", () => {
    render(<Gauge counts={50} />);

    expect(screen.getByText("counts 50 of 100")).toBeInTheDocument();
    expect(inWords(50)).toBe("counts 50 of 100");
    // At nought it says what a chip says of a thing that counts for nothing.
    expect(inWords(0)).toBe("does not count");
  });

  test("test_of_a_scale_it_says_which_end_and_how_far_towards_it_as_the_slider_of_a_scale_does", () => {
    const { rerender } = render(<Gauge counts={-60} ends={["Calm", "Buzzy"]} />);
    expect(screen.getByText("Towards Calm, 60 of 100")).toBeInTheDocument();
    expect(SLIDER.towards("Calm", 60)).toBe("Towards Calm, 60 of 100");

    rerender(<Gauge counts={40} ends={["Calm", "Buzzy"]} />);
    expect(screen.getByText("Towards Buzzy, 40 of 100")).toBeInTheDocument();

    // In the middle it says where it stands, in the words of the slider and in no other:
    // what the middle means is the slider's to say, in the line under it, and is said once.
    rerender(<Gauge counts={0} ends={["Calm", "Buzzy"]} />);
    expect(screen.getByText(SLIDER.middle)).toBeInTheDocument();
    expect(inWords(0, ["Calm", "Buzzy"])).toBe(SLIDER.middle);
    expect(SLIDER.middle).toMatch(/middle/);
    // It is never said to stand towards an end it does not stand towards.
    expect(screen.queryByText(/Towards/)).toBeNull();
  });

  test("test_what_is_drawn_is_for_the_eye_and_the_words_are_what_is_heard", () => {
    const { container } = render(<Gauge counts={50} />);

    expect(container.querySelector(".drawn")).toHaveAttribute("aria-hidden", "true");
    expect(container.querySelector(".words")?.closest("[aria-hidden]")).toBeNull();
    expect(screen.queryByRole("img")).toBeNull();
  });

  test("test_under_a_range_input_it_is_drawn_and_says_nothing", () => {
    const { container } = render(<Gauge counts={50} alone={false} />);

    expect(container.querySelector(".words")).toBeNull();
    expect(container.textContent).toBe("");
    expect(container.firstElementChild).toHaveAttribute("data-alone", "false");
    // It takes no press and no focus: what a person moves is the input that lies over it.
    expect(container.querySelector("button, input, a, [tabindex]")).toBeNull();
  });

  test("test_it_has_ten_steps_where_it_is_told_nothing_and_as_many_as_it_is_told", () => {
    const { container, rerender } = render(<Gauge counts={50} />);
    expect(STEPS).toBe(10);
    expect(cellsOf(container)).toHaveLength(10);

    rerender(<Gauge counts={50} steps={8} />);
    expect(cellsOf(container)).toHaveLength(8);

    // A scale has as many each way from its middle.
    rerender(<Gauge counts={50} steps={5} ends={["Calm", "Buzzy"]} />);
    expect(cellsOf(container)).toHaveLength(10);
    expect(container.querySelectorAll(".middle")).toHaveLength(1);
  });

  test("test_the_steps_fill_from_the_low_end_as_far_as_the_count_has_come", () => {
    const { container, rerender } = render(<Gauge counts={50} />);
    const filled = () => cellsOf(container).map((cell) => cell.dataset.full === "true");

    expect(filled()).toEqual([true, true, true, true, true, false, false, false, false, false]);
    // A step that is filled is the drawing of one, and an empty step the drawing of that.
    expect(cellsOf(container).map((cell) => cell.style.getPropertyValue("--art"))).toEqual([
      ...Array(5).fill('url("/art/gauge-cell-full.png")'),
      ...Array(5).fill('url("/art/gauge-cell.png")'),
    ]);

    rerender(<Gauge counts={80} />);
    expect(filled().filter(Boolean)).toHaveLength(8);
    // What is filled is one run from the low end, with no gap in it.
    expect(filled().join()).toBe([...Array(8).fill(true), false, false].join());
  });

  test("test_of_a_scale_the_steps_fill_from_the_middle_towards_the_end_that_is_asked_for", () => {
    const { container, rerender } = render(<Gauge counts={-60} steps={5} ends={["Calm", "Buzzy"]} />);
    const filled = () => cellsOf(container).map((cell) => cell.dataset.full === "true");

    expect(filled()).toEqual([false, false, true, true, true, false, false, false, false, false]);

    rerender(<Gauge counts={40} steps={5} ends={["Calm", "Buzzy"]} />);
    expect(filled()).toEqual([false, false, false, false, false, true, true, false, false, false]);

    rerender(<Gauge counts={0} steps={5} ends={["Calm", "Buzzy"]} />);
    expect(filled()).toEqual(Array(10).fill(false));
  });

  test("test_no_step_is_filled_only_at_nought_and_every_step_only_at_a_hundred", () => {
    const counts = Array.from({ length: 101 }, (_, count) => count);

    for (const steps of [5, 8, 10, 20]) {
      const filled = counts.map((count) => filledOf(count, steps));
      // A thing that counts a little is never drawn as one that counts for nothing, and one
      // that counts nearly all is never drawn as one that counts all.
      expect([steps, counts.filter((count) => filled[count] === 0)]).toEqual([steps, [0]]);
      expect([steps, counts.filter((count) => filled[count] === steps)]).toEqual([steps, [100]]);
      // More never fills fewer steps.
      expect([steps, counts.filter((count) => count > 0 && (filled[count] ?? 0) < (filled[count - 1] ?? 0))]).toEqual([steps, []]);
    }
    // Towards the low end of a scale it fills as it does towards the high end.
    expect([-100, -50, -1].map((count) => filledOf(count, 10))).toEqual([100, 50, 1].map((count) => filledOf(count, 10)));
  });

  test("test_a_count_is_held_between_what_a_gauge_can_show", () => {
    expect([-5, 0, 49.6, 100, 140, Number.NaN].map((count) => within(count))).toEqual([0, 0, 50, 100, 100, 0]);
    expect([-140, -100, -5].map((count) => within(count, -100))).toEqual([-100, -100, -5]);

    const { container } = render(<Gauge counts={140} />);
    expect(screen.getByText("counts 100 of 100")).toBeInTheDocument();
    expect(cellsOf(container).every((cell) => cell.dataset.full === "true")).toBe(true);
  });

  test("test_the_weight_stands_where_the_count_has_come_to_in_whole_art_pixels", () => {
    const row = STEPS * (CELL.width - 1) + 1;
    const at = (counts: number) => {
      const { container, unmount } = render(<Gauge counts={counts} />);
      const found = leftOf(markOf(container));
      unmount();
      return found;
    };

    expect(at(0)).toBe(0);
    expect(at(100)).toBe(row);
    expect(at(50)).toBe(Math.round(row / 2));
    // Never between two pixels, whatever the count: a drawing that stands there is blurred.
    const every = Array.from({ length: 101 }, (_, count) => at(count));
    expect(every.filter((left) => !Number.isInteger(left))).toEqual([]);
    expect(every.filter((left, count) => count > 0 && left < (every[count - 1] ?? 0))).toEqual([]);

    const { container } = render(<Gauge counts={50} />);
    expect(markOf(container).style.getPropertyValue("--art")).toBe('url("/art/ui-weight.png")');
  });

  test("test_it_is_as_wide_as_the_travel_of_a_thumb_that_is_as_wide_as_its_weight", () => {
    const { container } = render(<Gauge counts={50} />);
    const drawn = container.querySelector(".drawn") as HTMLElement;
    // Ten steps are 51 art pixels wide: each lies one art pixel over the one before it.
    const row = STEPS * (CELL.width - 1) + 1;
    const cells = cellsOf(container).map(leftOf);

    // The weight stands half its width in from either end at nought and at a hundred: so
    // the middle of the weight is where the middle of such a thumb is.
    expect(drawn.style.getPropertyValue("--wide")).toBe(String(row + MARK.width));
    expect(cells[0]).toBe(Math.floor(MARK.width / 2));
    // The steps stand side by side from there, and two of them share one outline.
    expect(row).toBe(51);
    expect(cells.map((left) => left - (cells[0] ?? 0))).toEqual(cells.map((_, index) => index * (CELL.width - 1)));
    // Nothing of it is laid outside its own box.
    expect(Math.max(...cells) + CELL.width).toBeLessThanOrEqual(row + MARK.width);
    expect(drawn.style.getPropertyValue("--high")).toBe(String(MARK.height + CELL.height - 1));
  });

  test("test_every_drawing_of_it_is_shown_at_its_own_size_and_is_never_stretched", () => {
    const drawn = STYLES.filter((rule) => [".cell", ".mark"].includes(rule.selector) && rule.sets.has("background"));

    expect(drawn.map((rule) => rule.sets.get("background"))).toEqual([
      "var(--art) 0 0 / calc(var(--px) * var(--w)) calc(var(--px) * var(--h)) no-repeat",
      "var(--art) 0 0 / calc(var(--px) * var(--w)) calc(var(--px) * var(--h)) no-repeat",
    ]);
    expect(drawn.map((rule) => rule.sets.get("image-rendering"))).toEqual(["pixelated", "pixelated"]);
    expect(drawn.map((rule) => rule.sets.get("inset-inline-start"))).toEqual([
      "calc(var(--px) * var(--left))",
      "calc(var(--px) * var(--left))",
    ]);
  });

  test("test_it_is_never_to_be_taken_for_where_a_place_sits_on_a_vibe", () => {
    const { container } = render(<Gauge counts={20} />);
    const pictures = new Set([...container.querySelectorAll<HTMLElement>("[style]")].map((one) => one.style.getPropertyValue("--art")).filter(Boolean));

    // It has more steps than a band has, it fills, and it is drawn with drawings of its own.
    expect(STEPS).toBeGreaterThan(5);
    expect([...pictures].sort()).toEqual([
      'url("/art/gauge-cell-full.png")',
      'url("/art/gauge-cell.png")',
      'url("/art/ui-weight.png")',
    ]);
    // Where a place sits is drawn with a peg, which a gauge never is: and with none of these.
    expect(/ui-peg/.test(readFileSync(path.join(__dirname, "Gauge.tsx"), "utf8"))).toBe(false);
    expect(/gauge-cell|ui-weight/.test(PEG)).toBe(false);
    expect(/"ui-peg"/.test(PEG)).toBe(true);
  });

  test("test_how_much_is_a_figure_and_is_set_in_the_reading_face", () => {
    const [words] = STYLES.filter((rule) => rule.selector === ".words");

    expect(words?.sets.get("font")).toBe("400 var(--size-small) / 1.3 var(--font-say)");
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <ul>
        <li>
          <Gauge counts={50} />
        </li>
        <li>
          <Gauge counts={0} />
        </li>
        <li>
          <Gauge counts={-60} steps={5} ends={["Calm", "Buzzy"]} />
        </li>
        <li>
          <label>
            Leafy
            <input type="range" min={0} max={100} defaultValue={50} />
          </label>
          <Gauge counts={50} alone={false} />
        </li>
      </ul>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
