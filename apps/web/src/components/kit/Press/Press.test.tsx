import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { faultsIn } from "../../../../test/support/axe";
import { rulesOf, subjectOf, type Rule } from "../../../../test/support/css";
import { cutOf, isDrawn, sizeOf } from "../drawings";
import { picturesOf, PRESS_KINDS } from "./kinds";
import { Press } from "./Press";

const CSS = readFileSync(path.join(__dirname, "Press.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const ALL = rulesOf(CSS);
const STYLES = ALL.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
const WELCOME = /prefers-reduced-motion:\s*no-preference/;
/** What the style sheet sets of a selector, where it holds always: one may be named by more rules than one. */
const setsOf = (selector: string) =>
  new Map(STYLES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

/** What a rule may set when it holds only under a press, the pointer or the focus: what is drawn, and never where. */
const DRAWN_ONLY = new Set([
  "background",
  "background-color",
  "background-image",
  "border-color",
  "border-image-source",
  "box-shadow",
  "color",
  "cursor",
  "outline",
  "outline-color",
  "outline-offset",
  "text-decoration",
  "text-decoration-thickness",
  "text-underline-offset",
]);
const underAPress = (rule: Rule) => /:active\b/.test(rule.selector);
/** True where the rule is for the button itself, and not for what is inside it or drawn before or after it. */
const isTheButton = (rule: Rule) => !/[\s>+~]/.test(rule.selector.trim()) && !/::/.test(subjectOf(rule.selector));
/** The pictures a button is drawn with, as the page names them on its face. */
const drawnOn = (button: HTMLElement) => {
  const face = button.firstElementChild as HTMLElement;
  return [face.style.getPropertyValue("--art"), face.style.getPropertyValue("--art-down")];
};

describe("a button, or a link drawn as one", () => {
  test("test_a_press_does_what_the_button_is_for", async () => {
    const onPress = jest.fn();
    render(<Press onPress={onPress}>Show the working</Press>);

    await userEvent.setup({ delay: null }).click(screen.getByRole("button", { name: "Show the working" }));

    expect(onPress).toHaveBeenCalledTimes(1);
  });

  test("test_it_is_a_native_button_of_the_size_of_a_main_control_and_sends_no_form_unless_told_to", () => {
    const { rerender } = render(<Press>Stop</Press>);
    const button = screen.getByRole("button", { name: "Stop" });

    expect(button.tagName).toBe("BUTTON");
    expect(button).toHaveClass("target");
    expect(button).toHaveAttribute("type", "button");

    rerender(<Press submits>Search</Press>);
    expect(screen.getByRole("button", { name: "Search" })).toHaveAttribute("type", "submit");
  });

  test("test_what_is_drawn_is_its_face_which_is_inside_the_button_that_takes_the_press", () => {
    render(<Press kind="go">Search</Press>);
    const button = screen.getByRole("button", { name: "Search" });

    // One thing is inside the button: its face, which is drawn, and on the face its words.
    expect(button.children).toHaveLength(1);
    expect(button.firstElementChild).toHaveClass("face");
    expect(button.firstElementChild?.children).toHaveLength(1);
    expect(button.firstElementChild?.firstElementChild).toHaveClass("says");
    expect(button.firstElementChild?.firstElementChild).toHaveTextContent("Search");
    // Nothing is drawn on the button itself: no edge, no ground and no room of its own.
    const itself = setsOf(".press");
    expect([itself.get("padding"), itself.get("border"), itself.get("background")]).toEqual(["0", "0", "none"]);
  });

  test("test_with_an_address_it_is_a_link_and_the_page_it_leads_to_is_not_fetched_ahead", () => {
    render(<Press href="/vibes">Every vibe</Press>);
    const link = screen.getByRole("link", { name: "Every vibe" });

    expect(link).toHaveAttribute("href", "/vibes");
    expect(link).toHaveAttribute("data-prefetch", "false");
    expect(link).toHaveClass("target");
    expect(link.firstElementChild).toHaveClass("face");
    expect(screen.queryByRole("button")).toBeNull();
  });

  test("test_a_button_that_is_on_says_so_and_one_that_holds_no_state_says_nothing", () => {
    const { rerender } = render(<Press on>Renting</Press>);
    expect(screen.getByRole("button", { name: "Renting" })).toHaveAttribute("aria-pressed", "true");

    rerender(<Press on={false}>Renting</Press>);
    expect(screen.getByRole("button", { name: "Renting" })).toHaveAttribute("aria-pressed", "false");

    rerender(<Press>Renting</Press>);
    expect(screen.getByRole("button", { name: "Renting" })).not.toHaveAttribute("aria-pressed");
  });

  test("test_a_link_that_is_on_says_it_is_the_page_one_is_on", () => {
    render(
      <Press href="/vibes" on>
        Every vibe
      </Press>,
    );

    expect(screen.getByRole("link", { name: "Every vibe" })).toHaveAttribute("aria-current", "page");
  });

  test("test_a_button_that_is_off_says_so_keeps_the_focus_and_ignores_the_press", async () => {
    const onPress = jest.fn();
    const user = userEvent.setup({ delay: null });
    render(
      <Press kind="go" off onPress={onPress}>
        Reading
      </Press>,
    );
    const button = screen.getByRole("button", { name: "Reading" });

    await user.click(button);
    await user.keyboard("{Enter}");

    expect(onPress).not.toHaveBeenCalled();
    expect(button).toHaveAttribute("aria-disabled", "true");
    // Switched off, it would lose the focus while it had it.
    expect(button).not.toBeDisabled();
    expect(button).toHaveFocus();
  });

  test("test_what_is_seen_on_a_short_button_is_the_start_of_its_name", () => {
    render(<Press name="Compare: Alderwick">Compare</Press>);

    expect(screen.getByRole("button", { name: "Compare: Alderwick" })).toHaveTextContent("Compare");
  });

  test("test_a_button_that_opens_something_says_whether_it_is_open", () => {
    render(
      <Press expanded={false} controls="the-working">
        Show the working
      </Press>,
    );
    const button = screen.getByRole("button", { name: "Show the working" });

    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(button).toHaveAttribute("aria-controls", "the-working");
  });

  test("test_a_page_may_find_the_button_again_and_give_it_the_focus", () => {
    const found: { current: HTMLButtonElement | null } = { current: null };
    render(
      <Press ref={found} data-main id="first">
        Leafy
      </Press>,
    );
    const button = screen.getByRole("button", { name: "Leafy" });

    expect(found.current).toBe(button);
    expect(button).toHaveAttribute("data-main", "true");
    expect(button).toHaveAttribute("id", "first");
    found.current?.focus();
    expect(button).toHaveFocus();
  });

  test("test_a_mark_of_the_pages_own_says_nothing_of_the_state_of_a_button", () => {
    // What a button says of itself is what it was handed by name. A mark is a mark.
    render(
      <Press off data-main>
        Reading
      </Press>,
    );

    expect(screen.getByRole("button", { name: "Reading" })).toHaveAttribute("aria-disabled", "true");
    expect([...screen.getByRole("button").attributes].map((one) => one.name).sort()).toEqual([
      "aria-disabled",
      "class",
      "data-main",
      "type",
    ]);
  });

  test("test_words_that_hold_a_figure_or_run_to_a_sentence_are_set_in_the_reading_face", () => {
    const { rerender } = render(<Press>Start again</Press>);
    const words = () => screen.getByRole("button").querySelector(".says");
    expect(words()).toHaveAttribute("data-reads", "false");

    // A figure is read exactly, so no part waits to be told that there is one.
    rerender(<Press>Add the 4 that need no choice</Press>);
    expect(words()).toHaveAttribute("data-reads", "true");

    rerender(<Press reads>Set as a guide: dearer areas rank lower</Press>);
    expect(words()).toHaveAttribute("data-reads", "true");

    expect(setsOf('.says[data-reads="true"]').get("font")).toBe("700 var(--size-body) / 1.25 var(--font-say)");
    // A short label is a name, and is set in the face of names, which has one weight.
    expect(setsOf(".press").get("font")).toBe("400 var(--name-1) / 1 var(--font-name)");
    expect(setsOf(".press").get("font-synthesis")).toBe("none");
  });

  test.each(PRESS_KINDS)("test_every_kind_is_drawn_by_its_own_picture_and_by_the_picture_of_it_pressed: %s", (kind) => {
    render(<Press kind={kind}>Search</Press>);
    const name = { go: "ui-button-go", plain: "ui-button", stop: "ui-button-stop" }[kind];

    expect(drawnOn(screen.getByRole("button"))).toEqual([`url("/art/${name}.png")`, `url("/art/${name}-down.png")`]);
    expect(picturesOf(kind, false)).toEqual({ up: name, down: `${name}-down` });
    expect(screen.getByRole("button").firstElementChild).toHaveAttribute("data-kind", kind);
  });

  test.each(PRESS_KINDS)("test_what_is_on_is_amber_whatever_its_kind: %s", (kind) => {
    render(
      <Press kind={kind} on>
        Renting
      </Press>,
    );

    expect(drawnOn(screen.getByRole("button"))).toEqual(['url("/art/ui-button-on.png")', 'url("/art/ui-button-on-down.png")']);
    expect(screen.getByRole("button").firstElementChild).toHaveAttribute("data-kind", "on");
    // What is not on is drawn as its kind is.
    expect(picturesOf(kind, false).up).not.toBe("ui-button-on");
  });

  test("test_the_words_of_a_button_are_page_on_cobalt_and_ink_on_page_and_on_amber", () => {
    const colours = (kind: string) => [setsOf(`.face[data-kind="${kind}"]`).get("background-color"), setsOf(`.face[data-kind="${kind}"]`).get("color")];

    expect(colours("go")).toEqual(["var(--cobalt)", "var(--page)"]);
    expect(colours("on")).toEqual(["var(--amber)", undefined]);
    // Every other button is page, and its words are ink.
    expect([setsOf(".face").get("background-color"), setsOf(".press").get("color")]).toEqual(["var(--page)", "var(--ink)"]);
    expect(STYLES.filter((rule) => /data-kind="(plain|stop)"/.test(rule.selector))).toEqual([]);
  });

  test("test_the_picture_of_a_button_is_cut_in_nine_where_its_drawing_says_and_is_never_stretched", () => {
    const face = setsOf(".face");
    const cut = [3, 3, 4, 3];

    expect(face.get("border-image")).toBe(
      "var(--art) 3 3 4 3 fill / calc(var(--px) * 3) calc(var(--px) * 3) calc(var(--px) * 4) repeat",
    );
    // The edge of the face is as wide as the picture is cut, so that a pixel of it is a whole square of the screen.
    expect(face.get("border-width")).toBe("calc(var(--px) * 3) calc(var(--px) * 3) calc(var(--px) * 4)");
    expect(face.get("image-rendering")).toBe("pixelated");
    for (const kind of PRESS_KINDS) {
      for (const on of [false, true]) {
        const { up, down } = picturesOf(kind, on);
        expect([up, isDrawn(up), cutOf(up)]).toEqual([up, true, cut]);
        // Pressed, it is drawn on the canvas of the button up and is cut where that is cut.
        expect([down, isDrawn(down), cutOf(down), sizeOf(down)]).toEqual([down, true, cut, sizeOf(up)]);
      }
    }
    // The ground of the face is laid inside its edge, and not under it: it does not show through a notch.
    expect(face.get("background-clip")).toBe("padding-box");
  });

  test("test_the_picture_of_a_button_pressed_is_asked_for_with_the_page_and_not_at_its_first_press", () => {
    // Seen in a browser: the picture of a button pressed was asked for when a button of its
    // kind was first pressed. Until it had come the button was drawn with no edge at all:
    // Search, held down for the first time, was a flat patch of cobalt. So the face lays
    // that picture as a ground of no size, which is asked for with the page and never seen.
    const face = setsOf(".face");

    expect([face.get("background-image"), face.get("background-size"), face.get("background-repeat")]).toEqual([
      "var(--art-down)",
      "0 0",
      "no-repeat",
    ]);
    // What is seen of the ground of a face is its colour, as it was: no rule lays the picture at a size.
    expect(face.get("background-color")).toBe("var(--page)");
    const laid = ALL.filter(
      (rule) => rule.sets.has("background-size") || rule.sets.has("background-image") || /var\(|url\(/.test(rule.sets.get("background") ?? ""),
    );
    expect(laid.map((rule) => [rule.selector, rule.sets.get("background-size")])).toEqual([[".face", "0 0"]]);
    // Every button names the picture it is pressed into, so none asks for a picture that is not there.
    for (const kind of PRESS_KINDS) {
      for (const on of [false, true]) expect(isDrawn(picturesOf(kind, on).down)).toBe(true);
    }
  });

  test("test_with_forced_colours_no_picture_is_drawn_on_a_button_at_rest_or_pressed_and_it_keeps_its_size", () => {
    const forced = ALL.filter((rule) => /forced-colors/.test(rule.under ?? ""));
    const of = (selector: string) => forced.filter((rule) => rule.selector === selector).map((rule) => rule.sets.get("border-image-source"));

    // A picture is taken away by its source. Said as the whole of `border-image`, the build
    // makes nothing of it, and the picture is still there.
    expect([of(".face"), of(".press:active > .face"), of('.press[aria-disabled="true"] > .face')]).toEqual([["none"], ["none"], ["none"]]);
    expect(ALL.filter((rule) => (rule.sets.get("border-image") ?? "").trim() === "none").map((rule) => rule.selector)).toEqual([]);
    // Its edge keeps the width its picture had.
    expect(forced.flatMap((rule) => [...rule.sets.keys()]).filter((property) => /width|padding|height/.test(property))).toEqual([]);
  });

  test("test_under_a_press_nothing_is_set_on_the_button_itself_that_moves_it_or_changes_the_room_it_takes", () => {
    const pressed = STYLES.filter(underAPress);

    // Nothing at all is said of the button itself under a press. It is what takes the press.
    expect(pressed.filter(isTheButton).map((rule) => rule.selector)).toEqual([]);
    // Of its face, which is inside it: the picture gives way to the picture of the button pressed.
    expect(pressed.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      [".press:active > .face", [["border-image-source", "var(--art-down)"]]],
      [".press:active > .face > .says", [["transform", "translate(var(--px), var(--px))"]]],
    ]);
    // No state of the button, or of anything in it, sets a size, a place or the room a thing takes.
    const ROOM = /^(width|height|min-.*|max-.*|padding.*|margin.*|border|border-width|border-style|border-image|border-image-width|border-image-slice|border-image-outset|inset.*|top|right|bottom|left|display|position|font.*|line-height|translate|scale|rotate|flex.*|gap)$/;
    const states = STYLES.filter((rule) => /:(hover|focus|focus-visible|active)\b|\[aria-/.test(rule.selector));
    expect(states.length).toBeGreaterThan(3);
    expect(states.flatMap((rule) => [...rule.sets.keys()].filter((property) => ROOM.test(property)).map((property) => `${rule.selector} sets ${property}`))).toEqual([]);
    // Under a press, the pointer or the focus, all that is set is what is drawn, but for the words that step.
    const comesAndGoes = STYLES.filter((rule) => /:(hover|focus|focus-within|focus-visible|active)\b/.test(rule.selector));
    expect(
      comesAndGoes.flatMap((rule) => [...rule.sets.keys()].filter((property) => !DRAWN_ONLY.has(property)).map((property) => `${rule.selector} sets ${property}`)),
    ).toEqual([".press:active > .face > .says sets transform"]);
  });

  test("test_the_room_of_the_shadow_is_inside_the_button_from_the_start", () => {
    // The shadow of a button is in its picture, at its foot: the fourth row of what is cut
    // there. The face takes that room whether it is pressed or not, and the button with it.
    const face = setsOf(".face");

    expect(face.get("border-width")).toBe("calc(var(--px) * 3) calc(var(--px) * 3) calc(var(--px) * 4)");
    expect(face.get("border-style")).toBe("solid");
    expect([setsOf(".press").get("display"), setsOf(".press").get("align-items"), face.get("flex")]).toEqual([
      "inline-flex",
      "stretch",
      "1 1 auto",
    ]);
    // Nothing of a button is drawn outside it: no shadow is thrown, and nothing is set out past its edge.
    expect(STYLES.filter((rule) => rule.sets.has("box-shadow") || rule.sets.has("border-image-outset")).map((rule) => rule.selector)).toEqual([]);
    expect(STYLES.filter((rule) => [...rule.sets].some(([property, value]) => /^(margin|inset|top|left|right|bottom)/.test(property) && /-/.test(value)))).toEqual([]);
  });

  test("test_the_face_steps_where_the_system_does_not_welcome_movement_and_never_moves_over_time", () => {
    // The picture changes in one step. It is a change of what is drawn, and no movement:
    // so it is said where it always holds, and not only where movement is welcome.
    const redrawn = STYLES.filter((rule) => rule.selector === ".press:active > .face");
    expect(redrawn.map((rule) => rule.under)).toEqual([null]);
    // Nothing is eased, and nothing takes time.
    expect(ALL.filter((rule) => [...rule.sets.keys()].some((property) => /^(transition|animation)/.test(property)))).toEqual([]);
    // The words step with the face only where movement is welcome: one art pixel down and
    // one to the right, which is as far as the face steps in its picture.
    const words = STYLES.filter((rule) => underAPress(rule) && rule.sets.has("transform"));
    expect(words.map((rule) => [rule.selector, WELCOME.test(rule.under ?? ""), rule.sets.get("transform")])).toEqual([
      [".press:active > .face > .says", true, "translate(var(--px), var(--px))"],
    ]);
  });

  test("test_a_button_that_is_off_is_drawn_down_as_far_as_a_press_would_take_it", () => {
    expect([...setsOf('.press[aria-disabled="true"] > .face')]).toEqual([["border-image-source", "var(--art-down)"]]);
    expect(setsOf('.press[aria-disabled="true"] > .face > .says').get("transform")).toBe("translate(var(--px), var(--px))");
    // It is not pointed at as one to press, and keeps the colour of its words: nothing is dimmed.
    expect(setsOf('.press[aria-disabled="true"]').get("cursor")).toBe("default");
    expect(setsOf('.press[aria-disabled="true"]').get("color")).toBe("var(--ink)");
  });

  test("test_the_focus_is_shown_by_the_ring_every_control_has_which_the_button_does_not_take_off", () => {
    const outlines = STYLES.filter((rule) => rule.sets.has("outline") || rule.sets.has("outline-style"));

    expect(outlines).toEqual([]);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <p>
        <Press>Show the working</Press>
        <Press kind="go" submits>
          Search
        </Press>
        <Press kind="go" off>
          Reading
        </Press>
        <Press kind="stop">Stop</Press>
        <Press href="/vibes" on>
          Every vibe
        </Press>
        <Press on name="Renting, chosen">
          Renting
        </Press>
      </p>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
