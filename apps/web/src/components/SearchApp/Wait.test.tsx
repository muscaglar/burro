import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { STATUS } from "@/content/search";
import { WAIT } from "@/content/wait";

import { faultsIn } from "../../../test/support/axe";
import { heavier, rulesOf, weightOf } from "../../../test/support/css";
import { Wait } from "./Wait";

const CSS = readFileSync(path.join(__dirname, "Wait.module.css"), "utf8");
const RULES = rulesOf(CSS);
const ALWAYS = RULES.filter((rule) => rule.under === null);
const setsOf = (selector: string, rules = ALWAYS) =>
  new Map(rules.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

/** What a part of the page says to whoever hears it: its words, less what is drawn for the eye alone. */
function heardIn(part: Element): string {
  const copy = part.cloneNode(true) as Element;
  copy.querySelectorAll("[aria-hidden='true']").forEach((drawn) => drawn.remove());
  return copy.textContent ?? "";
}

describe("the wait, while a search is read", () => {
  test("test_burro_hops_centre_stage_with_the_words_the_page_uses_under_him", () => {
    const { container } = render(<Wait held={null} />);
    const burro = container.querySelector("[data-pose]");

    expect(burro).toHaveAttribute("data-pose", "hops");
    // Centre stage he is drawn at the art pixel of the stage, which is the larger.
    expect(burro).toHaveAttribute("data-stage", "true");
    expect(container.querySelectorAll("[data-pose]")).toHaveLength(1);
    // The words are the ones the line under the box says, and no others.
    expect(container.textContent).toBe(STATUS.reading);
    // They stand under him: he comes first in the box.
    const words = [...container.querySelectorAll("*")].find((one) => one.children.length === 0 && one.textContent === STATUS.reading);
    expect(Boolean((burro as Element).compareDocumentPosition(words as Element) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
  });

  test("test_where_a_control_asked_for_a_first_ranking_the_words_under_him_say_that_it_is_worked_out", () => {
    // Nothing is read there, so he does not say that a search is. The words are the ones the
    // line under the box says of that moment, and no others.
    const { container } = render(<Wait held={null} of="ranking" />);

    expect(container.textContent).toBe(WAIT.ranking);
    expect(container.querySelector("[data-pose]")).toHaveAttribute("data-pose", "hops");
    expect(heardIn(container)).toBe("");
    expect(WAIT.ranking).not.toBe(STATUS.reading);
  });

  test("test_he_stands_in_a_box_of_the_look_and_never_on_the_grass", () => {
    const { container } = render(<Wait held={null} />);
    const box = container.querySelector("[data-kind]");

    expect(box).toHaveAttribute("data-kind", "box");
    expect(box).toContainElement(container.querySelector("[data-pose]") as HTMLElement);
    expect(box?.textContent).toBe(STATUS.reading);
  });

  test("test_the_status_line_says_what_happens_and_the_wait_says_it_to_no_screen_reader_a_second_time", () => {
    // He says nothing to a screen reader. What happens is said in words by the line under
    // the box, which is a live region: said here as well, it would be heard twice.
    const { container } = render(<Wait held={null} />);

    expect(heardIn(container)).toBe("");
    expect(screen.queryByRole("img")).toBeNull();
    expect(screen.queryByRole("status")).toBeNull();
    expect(container.querySelector("button, a, input, [tabindex]")).toBeNull();
    // Where the results will stand says that they are on their way, as it did.
    expect(container.firstElementChild).toHaveAttribute("aria-busy", "true");
  });

  test("test_his_box_is_as_high_as_the_first_result_that_stood_where_he_hops", () => {
    // A sentence is sent with a result on the page. His box takes its place at its size, so
    // that nothing under him moves when he comes.
    const { container } = render(<Wait held={287} />);
    const wait = container.firstElementChild as HTMLElement;

    expect(wait.style.getPropertyValue("--held")).toBe("287px");
    expect(setsOf(".wait").get("min-height")).toBe("var(--held, var(--first-result))");
  });

  test("test_where_no_result_has_stood_his_box_is_as_high_as_a_first_result_is", () => {
    const { container } = render(<Wait held={null} />);
    const wait = container.firstElementChild as HTMLElement;
    const wide = RULES.filter((rule) => rule.under === "@media (min-width: 60rem)");

    expect(wait.style.getPropertyValue("--held")).toBe("");
    // Measured on the whole page, on the made-up city, at 390 by 844: a first result is
    // 374 px high, and what Burro understood of a plain search takes 206 px over it.
    expect([setsOf(".wait").get("--first-result"), setsOf(".wait").get("--understood")]).toEqual(["23.375rem", "12.875rem"]);
    // From 60rem a first result is higher than the window has room for under the box, 639
    // px of 900, and on a first search nothing stands under his box. There his box is as
    // high as leaves him in sight, and is lower than a result.
    expect(setsOf(".wait", wide).get("--first-result")).toBe("16rem");
    expect(parseFloat(setsOf(".wait").get("--first-result") ?? "")).toBeGreaterThan(
      parseFloat(setsOf(".wait", wide).get("--first-result") ?? ""),
    );
  });

  test("test_where_his_box_is_higher_than_the_window_has_room_for_he_stands_as_high_in_it_as_keeps_him_in_sight", () => {
    // Seen at 1440 by 900: a sentence was added to a search, and his box took the place of
    // the first result, which was 639 px high and began at 717. He hopped in the middle of
    // it, from 937 to 1087, under the foot of the window, and nobody saw him.
    const stands = setsOf(".meadow > [data-pose]");

    expect([...stands]).toEqual([
      ["position", "sticky"],
      ["inset-block", "var(--space-5)"],
    ]);
    // Where he has room he is centre stage, as he was: the grass is laid out round its middle.
    expect(setsOf(".meadow").get("align-content")).toBe("center");
    // It weighs more than what the kit says of where he lies, whichever sheet is read last.
    const kit = rulesOf(readFileSync(path.join(__dirname, "..", "kit", "Burro", "Burro.module.css"), "utf8"));
    const lies = kit.filter((rule) => rule.sets.has("position") && /^\.burro\b/.test(rule.selector)).map((rule) => rule.selector);
    expect(lies).toEqual([".burro"]);
    for (const selector of lies) expect(heavier(weightOf(".meadow > [data-pose]"), weightOf(selector))).toBe(true);
    // He is found by what he is, and the page draws him so.
    const { container } = render(<Wait held={639} />);
    expect(container.querySelector("[data-pose]")?.parentElement?.className).toMatch(/meadow/);
  });

  test("test_nothing_that_holds_his_words_has_a_fixed_height", () => {
    // Text can be made larger. His box grows with its words, and is never cut.
    const fixed = RULES.filter((rule) => rule.sets.has("height") || rule.sets.has("max-height") || /hidden|clip/.test(rule.sets.get("overflow") ?? ""));

    expect(fixed.map((rule) => rule.selector)).toEqual([]);
    for (const [, length] of RULES.flatMap((rule) => [...rule.sets]).filter(([property]) => property === "min-height")) {
      expect(length).toMatch(/var\(--|rem\b/);
    }
  });

  test("test_nothing_of_the_wait_moves_but_the_rabbit_himself", () => {
    const moving = RULES.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition|transform)/.test(property)));

    expect(moving.map((rule) => rule.selector)).toEqual([]);
    expect(/@keyframes/.test(CSS)).toBe(false);
  });

  test("test_the_soil_he_throws_up_flies_in_his_own_box_and_the_wait_lays_nothing_out_for_it", () => {
    // The founder: "make soil flick up as it burros". The part that draws him draws it, in
    // his box, which is of one size whatever flies in it: so nothing of the wait moves or
    // makes room when it flies, and its sheet knows nothing of it.
    const { container } = render(<Wait held={null} />);
    const he = container.querySelector("[data-pose]") as HTMLElement;
    const soil = [...container.querySelectorAll<HTMLElement>('[style*="burro-hops-soil"]')];

    expect(soil).toHaveLength(1);
    expect(he).toContainElement(soil[0] as HTMLElement);
    expect(/soil/i.test(CSS)).toBe(false);
    // It is dress, as he is: nothing of it is heard.
    expect(soil[0]?.closest("[aria-hidden='true']")).not.toBeNull();
    expect(heardIn(container)).toBe("");
  });

  test("test_the_grass_he_hops_on_is_the_ground_of_the_page_and_goes_when_the_ground_is_turned_off", () => {
    const meadow = setsOf(".meadow");

    // The ground is named by its token, so that one line of the tokens turns it off here
    // too. Under it is the flat ground, which is what is left.
    expect(meadow.get("background")).toBe(
      "var(--lea) var(--ground) 0 0 / calc(var(--px-ground) * 192) calc(var(--px-ground) * 192)",
    );
    expect(meadow.get("image-rendering")).toBe("pixelated");
    expect(/\/art\//.test(CSS)).toBe(false);
    // No word stands on it: what is read is read on the cream of the box.
    const { container } = render(<Wait held={null} />);
    const grass = container.querySelector("[data-pose]")?.parentElement as HTMLElement;
    expect(grass.textContent).toBe("");
  });

  test("test_the_words_under_him_are_a_short_label_in_the_face_of_names", () => {
    const words = setsOf(".says");

    expect(words.get("font")).toBe("400 var(--name-2) / 1.1 var(--font-name)");
    expect(words.get("font-synthesis")).toBe("none");
    expect(words.get("color")).toBe("var(--ink)");
  });

  test("test_the_wait_has_no_accessibility_fault", async () => {
    const { container } = render(
      <section aria-label="Results">
        <Wait held={300} />
      </section>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
