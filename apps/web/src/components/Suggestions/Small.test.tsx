import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { faultsIn } from "../../../test/support/axe";
import { asWritten } from "../../../test/support/contrast";
import { rulesOf } from "../../../test/support/css";
import { Small } from "./Small";

const CSS = readFileSync(path.join(__dirname, "Small.module.css"), "utf8");
const RULES = rulesOf(CSS);
const AT_REST = RULES.filter((rule) => rule.under === null);
const setsOf = (selector: string, rules = AT_REST) =>
  new Map(rules.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));
/** The button of the kit, which a small one is drawn as. */
const KIT = rulesOf(readFileSync(path.join(__dirname, "..", "kit", "Press", "Press.module.css"), "utf8"));

describe("a small button of the look", () => {
  test("test_it_is_a_native_button_of_the_size_of_a_small_control_that_does_what_it_is_told", async () => {
    const pressed = jest.fn();
    render(<Small onPress={pressed}>Show it</Small>);
    const button = screen.getByRole("button", { name: "Show it" });

    expect(button.tagName).toBe("BUTTON");
    expect(button).toHaveAttribute("type", "button");
    expect(button).toHaveClass("small", "target-min");
    // It holds no state: it says nothing of being pressed, open or off.
    for (const said of ["aria-pressed", "aria-expanded", "aria-disabled"]) expect(button).not.toHaveAttribute(said);

    await userEvent.setup({ delay: null }).click(button);
    expect(pressed).toHaveBeenCalledTimes(1);
  });

  test("test_it_bears_the_whole_name_where_what_is_seen_is_the_start_of_it", () => {
    render(<Small name="Show the words in the box: Pubs and bars" onPress={jest.fn()}>Show the words</Small>);

    expect(screen.getByRole("button", { name: "Show the words in the box: Pubs and bars" })).toHaveTextContent("Show the words");
  });

  test("test_it_is_drawn_by_the_pictures_of_the_button_of_the_kit_at_the_pixel_of_a_phone", () => {
    // Seen in a browser: "Show in the box" and "Show the words" were plain words in a plain
    // edge, beside buttons of the look. A button of the kit is 44 px high and no less, which
    // there would stand between the box and the first result.
    render(<Small onPress={jest.fn()}>Show it</Small>);
    const face = screen.getByRole("button").firstElementChild as HTMLElement;

    expect([face.style.getPropertyValue("--art"), face.style.getPropertyValue("--art-down")]).toEqual([
      'url("/art/ui-button.png")',
      'url("/art/ui-button-down.png")',
    ]);
    // It is cut where the button of the kit is cut, and drawn at two pixels of the screen to
    // one of the drawing on every screen: three at the top and the sides, four at the foot.
    const cut = setsOf(".face", KIT.filter((rule) => rule.under === null)).get("border-image") ?? "";
    expect(cut).toContain(" 3 3 4 3 fill ");
    expect(setsOf(".face").get("border-image")).toBe(
      "var(--art) 3 3 4 3 fill / calc(var(--px-small) * 3) calc(var(--px-small) * 3) calc(var(--px-small) * 4) repeat",
    );
    expect(setsOf(".face").get("border-width")).toBe(
      "calc(var(--px-small) * 3) calc(var(--px-small) * 3) calc(var(--px-small) * 4)",
    );
    expect(setsOf(".face").get("image-rendering")).toBe("pixelated");
    // Under its picture are an edge of ink and cream, which are what is seen until the picture comes.
    expect([setsOf(".face").get("border-color"), setsOf(".face").get("background-color")]).toEqual([
      "var(--ink)",
      "var(--page)",
    ]);
  });

  test("test_its_words_are_a_short_label_in_the_face_of_names_and_it_is_lower_than_a_main_control", () => {
    const button = setsOf(".small");
    const tokens = asWritten();
    const pixel = Number.parseInt(tokens["--px-small"] ?? "", 10);

    expect(button.get("font")).toBe("400 var(--name-1) / 1 var(--font-name)");
    expect(button.get("font-synthesis")).toBe("none");
    expect(button.get("color")).toBe("var(--ink)");
    expect(button.get("min-height")).toBe("var(--target-min)");
    // Its face is its words and its edge: 20 px and seven art pixels, which is 34.
    const high = Number.parseFloat(tokens["--name-1"] ?? "") * 16 + 7 * pixel;
    expect(high).toBe(34);
    expect(high).toBeLessThan(Number.parseInt(tokens["--target"] ?? "", 10));
    expect(high).toBeGreaterThanOrEqual(Number.parseInt(tokens["--target-min"] ?? "", 10));
  });

  test("test_the_button_may_be_larger_than_its_face_and_the_face_stays_as_high_as_it_is", () => {
    // Where it stands at the end of a line that is higher than it, the whole of its place
    // takes the press, and what is drawn is no higher for it.
    expect(setsOf(".small").get("align-items")).toBe("center");
    expect(setsOf(".face").get("flex")).toBe("0 1 auto");
  });

  test("test_under_a_press_the_picture_gives_way_and_the_button_stays_where_it_is_and_as_large_as_it_is", () => {
    const keyed = RULES.filter((rule) => /:(hover|focus|focus-visible|active)\b/.test(rule.selector) && !/forced-colors/.test(rule.under ?? ""));

    expect(keyed.map((rule) => [rule.under, rule.selector, [...rule.sets]])).toEqual([
      [null, ".small:active > .face", [["border-image-source", "var(--art-down)"]]],
      [
        "@media (prefers-reduced-motion: no-preference)",
        ".small:active > .face > .says",
        [["transform", "translate(var(--px-small), var(--px-small))"]],
      ],
    ]);
    expect(RULES.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition)/.test(property)))).toEqual([]);
  });

  test("test_with_forced_colours_the_picture_is_taken_away_by_its_source", () => {
    const forced = RULES.filter((rule) => /forced-colors/.test(rule.under ?? ""));

    expect(setsOf(".face", forced).get("border-image-source")).toBe("none");
    expect(setsOf(".small:active > .face", forced).get("border-image-source")).toBe("none");
    expect(forced.filter((rule) => rule.sets.get("border-image") === "none")).toEqual([]);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(<Small onPress={jest.fn()}>Show it</Small>);

    expect(await faultsIn(container)).toEqual([]);
  });
});
