import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { faultsIn } from "../../../../test/support/axe";
import { rulesOf } from "../../../../test/support/css";
import { sizeOf } from "../drawings";
import { Art } from "./Art";

const STYLES = rulesOf(readFileSync(path.join(__dirname, "Art.module.css"), "utf8"));

describe("one drawing", () => {
  test("test_a_drawing_with_words_is_a_picture_that_says_them", () => {
    render(<Art name="ui-key" alt="A key" />);

    expect(screen.getByRole("img")).toHaveAccessibleName("A key");
  });

  test("test_a_drawing_with_no_words_is_kept_from_a_screen_reader", () => {
    const { container } = render(<Art name="ui-key" alt="" />);

    expect(screen.queryByRole("img")).toBeNull();
    expect(container.firstElementChild).toHaveAttribute("aria-hidden", "true");
  });

  test("test_a_drawing_is_shown_at_its_own_size_in_art_pixels_and_from_the_websites_own_origin", () => {
    const { container } = render(<Art name="ui-key" alt="" />);
    const drawn = container.firstElementChild as HTMLElement;
    const { width, height } = sizeOf("ui-key");

    expect(drawn.style.getPropertyValue("--w")).toBe(String(width));
    expect(drawn.style.getPropertyValue("--h")).toBe(String(height));
    expect(drawn.style.getPropertyValue("--art")).toBe('url("/art/ui-key.png")');
  });

  test("test_a_drawing_is_never_stretched_nor_shown_at_a_percentage_and_its_pixels_keep_a_hard_edge", () => {
    const [art] = STYLES.filter((rule) => rule.selector === ".art" && rule.under === null);

    expect(art?.sets.get("width")).toBe("calc(var(--px) * var(--w))");
    expect(art?.sets.get("height")).toBe("calc(var(--px) * var(--h))");
    expect(art?.sets.get("image-rendering")).toBe("pixelated");
    expect([...(art?.sets.values() ?? [])].filter((value) => value.includes("%"))).toEqual([]);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <p>
        <Art name="ui-key" alt="A key" />
        <Art name="thing-journey" alt="" />
      </p>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
