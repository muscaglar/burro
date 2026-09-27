import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { faultsIn } from "../../../../test/support/axe";
import { rulesOf } from "../../../../test/support/css";
import { faceOf, sizeOf } from "../drawings";
import { Pennant } from "./Pennant";

const STYLES = rulesOf(readFileSync(path.join(__dirname, "Pennant.module.css"), "utf8")).filter(
  (rule) => !/forced-colors/.test(rule.under ?? ""),
);
const setsOf = (selector: string) =>
  new Map(STYLES.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

/** A pennant as it is drawn, with its number taken out: what is left is the same for every rank. */
function drawnOf(rank: number) {
  const { container, unmount } = render(<Pennant rank={rank} />);
  const pennant = container.firstElementChild as HTMLElement;
  const drawn = {
    classes: [...pennant.querySelectorAll("*")].map((part) => part.className),
    style: pennant.getAttribute("style"),
    className: pennant.className,
    // Whatever it says of itself it says of every rank alike: no mark is kept for the first.
    attributes: [...pennant.attributes].map((one) => `${one.name}=${one.value}`).sort(),
    inside: [...pennant.querySelectorAll("*")].map((part) => [...part.attributes].map((one) => `${one.name}=${one.value}`).sort()),
  };
  unmount();
  return drawn;
}

describe("the rank of a result", () => {
  test("test_it_says_the_rank_in_words_and_draws_the_number_for_the_eye", () => {
    const { container } = render(<Pennant rank={3} />);

    expect(screen.getByText("Rank 3")).toHaveClass("visually-hidden");
    expect(container.querySelector(".figure")).toHaveTextContent("3");
    expect(container.querySelector(".figure")).toHaveAttribute("aria-hidden", "true");
    // It is heard once.
    expect(container.textContent).toBe("Rank 33");
  });

  test("test_the_pennant_of_the_first_is_the_pennant_of_the_tenth", () => {
    // Nobody wins: one drawing, one colour and one size, whatever the rank.
    const first = drawnOf(1);

    for (const rank of [2, 3, 10, 20]) expect([rank, drawnOf(rank)]).toEqual([rank, first]);
    expect(first.style).toContain('url("/art/ui-flag.png")');
    // No rule of the style sheet knows one rank from another.
    expect(STYLES.filter((rule) => /\[|:(first|last|nth)-/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
    expect(STYLES.map((rule) => rule.selector).sort()).toEqual([".figure", ".pennant"]);
  });

  test("test_the_pennant_is_shown_at_its_own_size_and_the_number_is_set_on_the_face_it_leaves_bare", () => {
    const { container } = render(<Pennant rank={1} />);
    const pennant = container.firstElementChild as HTMLElement;
    const { width, height } = sizeOf("ui-flag");
    const face = faceOf("ui-flag");
    const handed = (name: string) => pennant.style.getPropertyValue(name);

    expect([handed("--w"), handed("--h")]).toEqual([String(width), String(height)]);
    expect([handed("--left"), handed("--top"), handed("--wide"), handed("--high")]).toEqual(
      [face.left, face.top, face.width, face.height].map(String),
    );
    // The face lies on the pennant, and is large enough for a number to be read on it.
    expect(face.left + face.width).toBeLessThanOrEqual(width);
    expect(face.top + face.height).toBeLessThanOrEqual(height);
    expect(face.height).toBeGreaterThanOrEqual(7);
    expect(face.width).toBeGreaterThanOrEqual(11);

    expect(setsOf(".pennant").get("background")).toBe(
      "var(--art) 0 0 / calc(var(--px) * var(--w)) calc(var(--px) * var(--h)) no-repeat",
    );
    expect(setsOf(".pennant").get("image-rendering")).toBe("pixelated");
    expect([setsOf(".figure").get("inset-inline-start"), setsOf(".figure").get("inset-block-start")]).toEqual([
      "calc(var(--px) * var(--left))",
      "calc(var(--px) * var(--top))",
    ]);
    expect([setsOf(".figure").get("width"), setsOf(".figure").get("height")]).toEqual([
      "calc(var(--px) * var(--wide))",
      "calc(var(--px) * var(--high))",
    ]);
  });

  test("test_the_number_is_a_figure_and_is_set_in_the_reading_face_in_ink", () => {
    const figure = setsOf(".figure");

    expect(figure.get("font")).toBe(
      "700 calc(var(--px) * min(var(--high) * 0.9, var(--wide) * 1.5 / var(--figures))) / 1 var(--font-say)",
    );
    expect(figure.get("color")).toBe("var(--ink)");
    // It is sized as the drawing is, and never by the type of the browser: it keeps to its pennant.
    expect(figure.get("white-space")).toBe("nowrap");
  });

  test("test_a_rank_of_three_figures_is_set_smaller_and_stays_on_its_pennant", () => {
    const figuresOf = (rank: number) => {
      const { container, unmount } = render(<Pennant rank={rank} />);
      const said = (container.firstElementChild as HTMLElement).style.getPropertyValue("--figures");
      unmount();
      return Number(said);
    };
    const face = faceOf("ui-flag");
    /** The size of the number, in art pixels, as the style sheet works it out: a figure is given two thirds of its size. */
    const sizeAt = (figures: number) => Math.min(face.height * 0.9, (face.width * 1.5) / figures);
    /**
     * How wide a heavy figure of the reading face is, of its size, where every figure is of
     * one width. Measured in a browser: 66.25 px at 100 px. The face before it was narrower,
     * 0.634, and a rank of three figures set to that stood 0.4 of an art pixel off its pennant.
     */
    const WIDE = 0.663;
    expect(WIDE).toBeLessThanOrEqual(2 / 3);

    // One figure is set as two are: the first has the pennant of the tenth, and its number is as large.
    expect([1, 9, 10, 99].map(figuresOf)).toEqual([2, 2, 2, 2]);
    expect([100, 101].map(figuresOf)).toEqual([3, 3]);
    for (const [rank, figures] of [[9, 1], [10, 2], [99, 2], [100, 3]] as const) {
      const wide = figures * WIDE * sizeAt(figuresOf(rank));
      expect([rank, wide <= face.width]).toEqual([rank, true]);
    }
    // Two figures are as high as the face lets them be, and three are still read: 12 px at the least on a phone.
    expect(sizeAt(2)).toBe(face.height * 0.9);
    expect(sizeAt(3) * 2).toBeGreaterThanOrEqual(12);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <p>
        <Pennant rank={1} />
        <Pennant rank={10} />
      </p>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
