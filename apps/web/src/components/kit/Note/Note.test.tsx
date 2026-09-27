import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Link from "next/link";

import { SOURCE } from "@/content/search";

import { faultsIn } from "../../../../test/support/axe";
import { rulesOf } from "../../../../test/support/css";
import { sizeOf } from "../drawings";
import { Note } from "./Note";

const CSS = readFileSync(path.join(__dirname, "Note.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const ALL = rulesOf(CSS);
const STYLES = ALL.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
const setsOf = (selector: string) =>
  new Map(STYLES.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

function show(props: Partial<Parameters<typeof Note>[0]> = {}) {
  const view = render(
    <div>
      <p>A sentence of the API.</p>
      <Note {...props}>Synthetic test data. Data from 2025.</Note>
    </div>,
  );
  return { user: userEvent.setup({ delay: null }), ...view };
}
const key = () => screen.getByRole("button");

describe("the key of a source", () => {
  test("test_a_press_opens_the_source_in_place_and_a_second_press_closes_it", async () => {
    const { user } = show();
    expect(screen.queryByText("Synthetic test data. Data from 2025.")).toBeNull();

    await user.click(key());
    expect(screen.getByText("Synthetic test data. Data from 2025.")).toBeVisible();
    expect(key()).toHaveAttribute("aria-expanded", "true");

    await user.click(key());
    expect(screen.queryByText("Synthetic test data. Data from 2025.")).toBeNull();
    expect(key()).toHaveAttribute("aria-expanded", "false");
  });

  test("test_the_key_says_source_and_keeps_saying_it_when_it_opens", async () => {
    const { user } = show();

    expect(key()).toHaveAccessibleName(SOURCE.button);
    await user.click(key());
    expect(key()).toHaveAccessibleName("Source");
  });

  test("test_a_key_may_say_what_it_is_the_source_of_to_tell_it_from_the_next", () => {
    show({ name: "Source for reason 1" });

    expect(screen.getByRole("button", { name: "Source for reason 1" })).toHaveTextContent("Source");
  });

  test("test_it_is_a_native_button_and_a_small_control", () => {
    show();

    expect(key().tagName).toBe("BUTTON");
    expect(key()).toHaveAttribute("type", "button");
    expect(key()).toHaveClass("target-min");
  });

  test("test_what_it_opens_stands_next_after_the_key_so_that_a_sentence_lays_both_out_as_it_always_has", () => {
    const { container } = show({ openAtFirst: true });
    const note = key().parentElement as HTMLElement;

    // The website lays a sentence and its source out by this: what holds the key holds the
    // key and then what it opens, and nothing else.
    expect(note.tagName).toBe("DIV");
    expect([...note.children].map((part) => part.tagName)).toEqual(["BUTTON", "DIV"]);
    expect(key()).toHaveAttribute("aria-controls", note.children[1]?.id);
    expect(container.querySelector("button[aria-expanded] + div")).toHaveTextContent("Synthetic test data");
  });

  test("test_the_keyboard_opens_it_and_escape_closes_it_and_puts_the_focus_back_on_the_key", async () => {
    const { user } = show();

    await user.tab();
    expect(key()).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(key()).toHaveAttribute("aria-expanded", "true");

    await user.keyboard("{Escape}");
    expect(key()).toHaveAttribute("aria-expanded", "false");
    expect(key()).toHaveFocus();
  });

  test("test_escape_from_inside_what_it_opened_puts_the_focus_back_on_the_key_and_never_on_nothing", async () => {
    const user = userEvent.setup({ delay: null });
    render(
      <div>
        <Note>
          <Link href="/sources#synthetic" prefetch={false}>
            Synthetic test data
          </Link>
        </Note>
      </div>,
    );

    await user.click(key());
    await user.tab();
    expect(screen.getByRole("link", { name: "Synthetic test data" })).toHaveFocus();

    // What had the focus goes when the source closes. The focus does not go with it.
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("link")).toBeNull();
    expect(key()).toHaveFocus();
  });

  test("test_it_may_stand_open_at_first_and_the_page_may_decide_whether_it_is_open", async () => {
    const onToggle = jest.fn();
    const { user, rerender } = show({ open: true, onToggle });
    expect(key()).toHaveAttribute("aria-expanded", "true");

    await user.click(key());
    expect(onToggle.mock.calls).toEqual([[false]]);
    // It is the page's to say: until the page says otherwise, it is open.
    expect(key()).toHaveAttribute("aria-expanded", "true");

    rerender(
      <div>
        <Note open={false}>Synthetic test data. Data from 2025.</Note>
      </div>,
    );
    expect(key()).toHaveAttribute("aria-expanded", "false");
  });

  test("test_the_key_is_the_drawing_of_a_key_shown_at_its_own_size_and_kept_from_a_screen_reader", () => {
    const { container } = show();
    const drawn = container.querySelector(".drawn") as HTMLElement;
    const { width, height } = sizeOf("ui-key");

    expect(drawn.style.getPropertyValue("--art")).toBe('url("/art/ui-key.png")');
    expect([drawn.style.getPropertyValue("--w"), drawn.style.getPropertyValue("--h")]).toEqual([String(width), String(height)]);
    expect(drawn).toHaveAttribute("aria-hidden", "true");
    expect(setsOf(".drawn").get("background")).toBe(
      "var(--art) 0 0 / calc(var(--px) * var(--w)) calc(var(--px) * var(--h)) no-repeat",
    );
    expect(setsOf(".drawn").get("image-rendering")).toBe("pixelated");
  });

  test("test_open_or_in_hand_the_key_stands_on_amber_and_nothing_of_it_moves_or_changes_size", () => {
    const states = STYLES.filter((rule) => /:(hover|focus-visible|focus|active)\b|\[aria-expanded/.test(rule.selector));

    expect(states.map((rule) => rule.selector).sort()).toEqual([".key:focus-visible", ".key:hover", '.key[aria-expanded="true"]']);
    expect(states.map((rule) => [...rule.sets])).toEqual(states.map(() => [["background-color", "var(--amber)"]]));
    // Amber is not told from page by everyone: the rule of ink under the key is there in every state.
    expect(setsOf(".key").get("border-block-end")).toBe("var(--px) solid var(--ink)");
  });

  test("test_a_source_and_a_date_are_read_on_cream_and_are_set_in_the_reading_face_in_ink", () => {
    const opened = setsOf(".opened");

    expect(opened.get("font")).toBe("400 var(--size-small) / 1.4 var(--font-say)");
    expect(opened.get("color")).toBe("var(--ink)");
    // It stood on sand. A sentence and a figure are read on cream, and what a source opens
    // holds both, and the name of a source, which is a link in the colour of one: on sand
    // ink alone is read. It is told from the card it stands in by its solid edge of ink.
    expect(opened.get("background")).toBe("var(--page)");
    expect(opened.get("border")).toBe("var(--px) solid var(--ink)");
    expect(STYLES.filter((rule) => /var\(--sand\)/.test([...rule.sets.values()].join(" "))).map((rule) => rule.selector)).toEqual([]);
    // The word on the key is a short label, in the face of names.
    expect(setsOf(".key").get("font")).toBe("400 var(--name-1) / 1 var(--font-name)");
  });

  test("test_no_edge_of_it_is_drawn_in_dashes_or_in_dots_with_forced_colours_as_without", () => {
    // A person who walked the website did not know what a dashed edge was for. What a key
    // opens had one, drawn in art pixels as a run of ink and sand that repeats.
    expect(/dashed|dotted|repeating-linear-gradient/.test(CSS)).toBe(false);
    expect(ALL.filter((rule) => /transparent/.test(rule.sets.get("border") ?? rule.sets.get("border-color") ?? "")).map((rule) => rule.selector)).toEqual([]);
    expect(ALL.filter((rule) => rule.selector === ".opened" && rule.sets.has("border")).map((rule) => [rule.under, rule.sets.get("border")])).toEqual([
      [null, "var(--px) solid var(--ink)"],
      ["@media (forced-colors: active)", "var(--px) solid CanvasText"],
    ]);
  });

  test("test_what_is_not_open_takes_no_room_and_is_not_on_the_page", () => {
    const { container } = show();

    expect(container.querySelector("button + div")).toHaveAttribute("hidden");
    expect(container.querySelector("button + div")?.textContent).toBe("");
    expect(setsOf(".opened[hidden]").get("display")).toBe("none");
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <div>
        <Note name="Source for reason 1">Synthetic test data.</Note>
        <Note name="Source for reason 2" openAtFirst>
          Synthetic test data. Data from 2025.
        </Note>
      </div>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
