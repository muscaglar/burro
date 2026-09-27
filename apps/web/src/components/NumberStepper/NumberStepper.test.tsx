import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { faultsIn } from "../../../test/support/axe";
import { heavier, rulesOf, weightOf } from "../../../test/support/css";
import { sizeOf } from "../kit/drawings";
import { NumberStepper } from "./NumberStepper";

const CSS = readFileSync(path.join(__dirname, "NumberStepper.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const STYLES = rulesOf(CSS).filter((rule) => !/forced-colors/.test(rule.under ?? ""));
/** What the style sheet sets of a selector, with every gap in a value made one. */
const setsOf = (selector: string) =>
  new Map(
    STYLES.filter((rule) => rule.selector === selector).flatMap((rule) =>
      [...rule.sets].map(([property, value]): [string, string] => [property, value.replace(/\s+/g, " ")]),
    ),
  );

function show(props: Partial<Parameters<typeof NumberStepper>[0]> = {}) {
  const onCommit = jest.fn();
  const onStep = jest.fn();
  const stepper = (more: Partial<Parameters<typeof NumberStepper>[0]>) => (
    <NumberStepper
      label="Longest journey"
      value={35}
      hint="Between 10 and 90 minutes."
      notANumber="Give a whole number."
      less="Shorter"
      more="Longer"
      onCommit={onCommit}
      onStep={onStep}
      version={1}
      {...props}
      {...more}
    />
  );
  const view = render(stepper({}));
  return {
    onCommit,
    onStep,
    user: userEvent.setup({ delay: null }),
    again: (more: Partial<Parameters<typeof NumberStepper>[0]>) => view.rerender(stepper(more)),
    ...view,
  };
}

const field = () => screen.getByRole("textbox", { name: "Longest journey" });

describe("a number with a minus and a plus", () => {
  test("test_a_typed_number_is_sent_when_the_field_is_left_and_never_key_by_key", async () => {
    const { user, onCommit } = show();

    await user.clear(field());
    await user.type(field(), "4");
    await user.type(field(), "5");
    expect(onCommit).not.toHaveBeenCalled();
    await user.tab();

    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(onCommit).toHaveBeenCalledWith(45);
  });

  test("test_enter_sends_the_number_too", async () => {
    const { user, onCommit } = show();

    await user.clear(field());
    await user.type(field(), "20{Enter}");

    expect(onCommit).toHaveBeenCalledWith(20);
  });

  test("test_a_number_that_did_not_change_is_not_sent", async () => {
    const { user, onCommit } = show();

    await user.clear(field());
    await user.type(field(), "35{Enter}");
    await user.click(field());
    await user.tab();

    expect(onCommit).not.toHaveBeenCalled();
  });

  test("test_a_button_sends_a_step_and_the_field_waits_for_where_the_api_says_it_landed", async () => {
    const { user, onStep, onCommit, again } = show();

    await user.click(screen.getByRole("button", { name: "Longer" }));
    await user.click(screen.getByRole("button", { name: "Shorter" }));

    expect(onStep.mock.calls).toEqual([["up_small"], ["down_small"]]);
    expect(onCommit).not.toHaveBeenCalled();
    expect(field()).toHaveValue("35");
    again({ value: 40, version: 2 });
    expect(field()).toHaveValue("40");
  });

  test("test_a_number_is_brought_within_the_limits_where_they_are_given", async () => {
    const { user, onCommit } = show({ keptWithin: { least: 10, most: 90 } });

    await user.clear(field());
    await user.type(field(), "500{Enter}");
    expect(onCommit).toHaveBeenLastCalledWith(90);
    expect(field()).toHaveValue("90");

    await user.clear(field());
    await user.type(field(), "3{Enter}");
    expect(onCommit).toHaveBeenLastCalledWith(10);
  });

  test("test_what_is_no_number_is_said_beside_the_field_and_not_sent", async () => {
    const { user, onCommit } = show();

    await user.clear(field());
    await user.type(field(), "half an hour{Enter}");

    expect(onCommit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("Give a whole number.");
    expect(field()).toBeInvalid();
    expect(field()).toHaveAccessibleDescription("Between 10 and 90 minutes. Give a whole number.");

    await user.type(field(), "{Backspace}");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("test_an_emptied_field_goes_back_to_what_the_api_said", async () => {
    const { user, onCommit } = show();

    await user.clear(field());
    await user.tab();

    expect(onCommit).not.toHaveBeenCalled();
    expect(field()).toHaveValue("35");
  });

  test("test_the_field_is_drawn_again_from_every_answer", async () => {
    const { user, again } = show();

    await user.clear(field());
    await user.type(field(), "1{Enter}");
    expect(field()).toHaveValue("1");

    // The answer came back with the number as it was: the change was refused.
    again({ value: 35, version: 2, problem: "That number is outside what Burro accepts." });
    expect(field()).toHaveValue("35");
    expect(screen.getByRole("alert")).toHaveTextContent("That number is outside what Burro accepts.");
  });

  test("test_an_answer_that_arrives_while_a_number_is_typed_leaves_the_typing_alone", async () => {
    const { user, again, onCommit } = show({ value: null });

    await user.click(field());
    await user.keyboard("18");
    // A sentence was being read, and its answer names a budget. It comes while the number is half typed.
    again({ value: 1700, version: 2 });
    expect(field()).toHaveValue("18");

    await user.keyboard("00");
    expect(field()).toHaveValue("1800");
    await user.tab();

    // What was typed is what is sent: no digit of the API's number was joined to it.
    expect(onCommit.mock.calls).toEqual([[1800]]);
  });

  test("test_typing_that_no_number_could_be_read_from_is_kept_when_an_answer_arrives", async () => {
    const { user, again, onCommit } = show();

    await user.clear(field());
    await user.type(field(), "half an hour{Enter}");
    again({ value: 40, version: 2 });

    expect(field()).toHaveValue("half an hour");
    expect(screen.getByRole("alert")).toHaveTextContent("Give a whole number.");
    expect(onCommit).not.toHaveBeenCalled();
  });

  test("test_once_the_number_is_sent_the_answer_to_it_is_taken_even_with_the_caret_in_the_field", async () => {
    const { user, again } = show();

    await user.clear(field());
    await user.type(field(), "45{Enter}");
    expect(field()).toHaveFocus();
    // The answer says where it landed, and the field shows that.
    again({ value: 44, version: 2 });

    expect(field()).toHaveValue("44");
  });

  test("test_an_answer_is_taken_by_a_field_nobody_is_typing_in", () => {
    const { again } = show();

    again({ value: 50, version: 2 });
    expect(field()).toHaveValue("50");
    // A spec may change with no answer counted, as when a reading comes while an edit waits.
    again({ value: 55, version: 2 });
    expect(field()).toHaveValue("55");
  });

  test("test_a_number_put_back_before_the_answer_comes_is_sent_so_that_the_one_waiting_is_undone", async () => {
    const { user, onCommit } = show();

    await user.clear(field());
    await user.type(field(), "45{Enter}");
    // No answer has come. The person thinks again, and types what was there before.
    await user.clear(field());
    await user.type(field(), "35{Enter}");

    expect(onCommit.mock.calls).toEqual([[45], [35]]);
  });

  test("test_the_same_number_sent_twice_before_the_answer_comes_is_sent_once", async () => {
    const { user, onCommit } = show();

    await user.clear(field());
    await user.type(field(), "45{Enter}");
    await user.clear(field());
    await user.type(field(), "45{Enter}");

    expect(onCommit.mock.calls).toEqual([[45]]);
  });

  test("test_after_the_answer_a_number_is_held_against_what_the_answer_said", async () => {
    const { user, again, onCommit } = show();

    await user.clear(field());
    await user.type(field(), "45{Enter}");
    // The answer refused it: the number is what it was.
    again({ value: 35, version: 2 });
    await user.clear(field());
    await user.type(field(), "35{Enter}");

    expect(onCommit.mock.calls).toEqual([[45]]);
  });

  test("test_a_number_typed_after_a_step_is_sent_even_if_it_is_the_number_the_api_last_said", async () => {
    const { user, again, onStep, onCommit } = show();

    await user.click(screen.getByRole("button", { name: "Longer" }));
    // The step is on its way, and where it lands is the API's to say. The person wants 35 after all.
    await user.clear(field());
    await user.type(field(), "35{Enter}");

    expect(onStep.mock.calls).toEqual([["up_small"]]);
    expect(onCommit.mock.calls).toEqual([[35]]);

    // Once the answer is in, 35 is what the API says, and typing it again sends nothing.
    again({ value: 35, version: 2 });
    await user.clear(field());
    await user.type(field(), "35{Enter}");
    expect(onCommit.mock.calls).toEqual([[35]]);
  });

  test("test_with_nothing_to_step_from_the_buttons_are_off", () => {
    show({ value: null, canStep: false });

    expect(screen.getByRole("button", { name: "Shorter" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Longer" })).toBeDisabled();
    expect(field()).toHaveValue("");
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = show({ problem: "That number is outside what Burro accepts." });

    expect(await faultsIn(container)).toEqual([]);
  });
});

/** The layers of a ground, the first of which is drawn over the rest. */
const layersOf = (ground: string) => ground.split(/,(?![^(]*\))/).map((layer) => layer.trim().replace(/\s+/g, " "));

describe("a number with a minus and a plus, as it is drawn", () => {
  const shorter = () => screen.getByRole("button", { name: "Shorter" });
  const longer = () => screen.getByRole("button", { name: "Longer" });

  test("test_each_button_is_native_is_named_for_what_it_does_and_is_the_size_of_a_main_control", () => {
    show();

    for (const button of [shorter(), longer()]) {
      expect(button.tagName).toBe("BUTTON");
      expect(button).toHaveAttribute("type", "button");
      expect(button).toHaveClass("target");
    }
    // The field is between them, in the order they are read in.
    expect(shorter().compareDocumentPosition(field()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(field().compareDocumentPosition(longer()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(field()).toHaveClass("target");
  });

  test("test_a_button_is_one_drawing_of_a_step_shown_whole_at_its_own_size_at_rest_and_pressed", () => {
    show();
    const handed = (button: HTMLElement) => ["--art", "--art-down", "--w", "--h"].map((name) => button.style.getPropertyValue(name));
    const { width, height } = sizeOf("btn-less");

    expect(handed(shorter())).toEqual(['url("/art/btn-less.png")', 'url("/art/btn-less-down.png")', String(width), String(height)]);
    expect(handed(longer())).toEqual(['url("/art/btn-more.png")', 'url("/art/btn-more-down.png")', String(width), String(height)]);
    // Its sign is in its drawing, and its name is in words: nothing is written on it.
    expect([shorter().textContent, longer().textContent]).toEqual(["", ""]);
    expect([setsOf(".step").get("width"), setsOf(".step").get("height")]).toEqual([
      "calc(var(--px) * var(--w))",
      "calc(var(--px) * var(--h))",
    ]);
    expect(layersOf(setsOf(".step").get("background") ?? "")[0]).toBe(
      "var(--art) 0 0 / calc(var(--px) * var(--w)) calc(var(--px) * var(--h)) no-repeat",
    );
    expect(setsOf(".step").get("image-rendering")).toBe("pixelated");
    // At two pixels of the screen to one of the drawing it is as large as a main control.
    expect([width * 2, height * 2]).toEqual([44, 44]);
  });

  test("test_the_drawing_of_a_button_pressed_is_asked_for_with_the_page_and_not_at_its_first_press", () => {
    // Seen in a browser, of the button of the kit: asked for at the first press, the
    // picture had not come, and the button was drawn with nothing on it. It is laid under
    // the drawing at rest, at no size, and over the ground of a button whose drawing has not come.
    const layers = layersOf(setsOf(".step").get("background") ?? "");

    expect(layers).toEqual([
      "var(--art) 0 0 / calc(var(--px) * var(--w)) calc(var(--px) * var(--h)) no-repeat",
      "var(--art-down) 0 0 / 0 0 no-repeat var(--page)",
    ]);
  });

  test("test_under_a_press_and_while_it_is_off_the_drawing_changes_and_nothing_moves_or_is_dimmed", () => {
    const states = STYLES.filter((rule) => /:(hover|focus|focus-visible|active|disabled)\b|\[aria-/.test(rule.selector));
    const pressed = "var(--page) var(--art-down) 0 0 / calc(var(--px) * var(--w)) calc(var(--px) * var(--h)) no-repeat";

    expect(states.map((rule) => rule.selector).sort()).toEqual([
      ".step:active",
      ".step:disabled",
      ".step:disabled",
      '.step[aria-disabled="true"]',
      '.step[aria-disabled="true"]',
    ]);
    expect([...new Set(states.flatMap((rule) => [...rule.sets.keys()]))].sort()).toEqual(["background", "cursor"]);
    // The drawing of the button pressed is shown at the size of the one at rest, in its place.
    for (const state of [".step:active", ".step:disabled", '.step[aria-disabled="true"]']) {
      expect([state, setsOf(state).get("background")]).toEqual([state, pressed]);
    }
    // Nothing is eased, nothing takes time and nothing is see-through.
    expect(STYLES.filter((rule) => [...rule.sets.keys()].some((property) => /^(transition|animation|opacity|filter)/.test(property)))).toEqual([]);
  });

  test("test_with_nothing_to_step_from_a_button_is_switched_off_and_takes_no_press", async () => {
    const { user, onStep } = show({ value: null, canStep: false });

    await user.click(longer());
    await user.click(shorter());

    expect(onStep).not.toHaveBeenCalled();
    expect(longer()).toBeDisabled();
  });

  test("test_the_number_is_read_so_it_is_set_in_the_reading_face_and_its_label_in_the_face_of_names", () => {
    expect(setsOf(".row > .field").get("font")).toBe("700 var(--size-lead) / 1.2 var(--font-say)");
    expect(setsOf(".row > .field").get("font-variant-numeric")).toBe("tabular-nums");
    expect(setsOf(".label").get("font")).toBe("400 var(--name-1) / 1.1 var(--font-name)");
    // The face of names has one weight and stands upright: a browser that thickens it smears it.
    expect(setsOf(".label").get("font-synthesis")).toBe("none");
  });

  test("test_a_label_that_holds_a_figure_is_read_and_is_set_in_the_reading_face", () => {
    const { again } = show();
    const label = () => (field() as HTMLInputElement).labels?.[0] as HTMLElement;

    expect(label()).toHaveAttribute("data-reads", "false");
    again({ label: "Longest journey, of 2 or more" });
    expect(screen.getByRole("textbox", { name: "Longest journey, of 2 or more" })).toBeInTheDocument();
    expect(screen.getByText("Longest journey, of 2 or more")).toHaveAttribute("data-reads", "true");
    expect(setsOf('.label[data-reads="true"]').get("font")).toBe("700 var(--size-body) / 1.2 var(--font-say)");
  });

  test("test_why_a_number_was_not_taken_is_said_in_ink_beside_an_edge_of_poppy", () => {
    show({ problem: "That number is outside what Burro accepts." });

    expect(screen.getByRole("alert")).toHaveClass("problem");
    expect(setsOf(".problem").get("color")).toBe("var(--error)");
    expect(setsOf(".problem").get("border-inline-start")).toBe("calc(var(--px) * 2) solid var(--error-edge)");
    // No ground of poppy is laid, and no word is set in it.
    expect(STYLES.filter((rule) => /poppy|error-edge/.test(rule.sets.get("background") ?? rule.sets.get("color") ?? ""))).toEqual([]);
  });

  test("test_the_field_weighs_more_than_what_the_page_says_of_every_field", () => {
    // Seen in a browser: the page's own rule for every field, which names the element and
    // what it is not, outweighed the class of this one, and gave it room at either hand
    // that left a hundred cut short. Which of two style sheets is read last is not the
    // website's to decide, so the field is named by what holds it as well.
    const base = rulesOf(readFileSync(path.join(__dirname, "..", "..", "styles", "base.css"), "utf8"));
    const ofEveryField = base.filter((rule) => /^input:not\(/.test(rule.selector) && rule.sets.has("padding"));
    const own = STYLES.filter((rule) => rule.sets.has("padding") && /\.field$/.test(rule.selector));

    expect(ofEveryField.map((rule) => weightOf(rule.selector))).toEqual([[0, 1, 1]]);
    expect(own.map((rule) => [rule.selector, heavier(weightOf(rule.selector), [0, 1, 1])])).toEqual([[".row > .field", true]]);
  });

  test("test_nothing_that_holds_words_has_a_height_of_its_own_and_what_does_not_fit_goes_under", () => {
    const high = STYLES.filter((rule) => rule.selector !== ".step" && (rule.sets.has("height") || rule.sets.has("max-height")));

    expect(high.map((rule) => rule.selector)).toEqual([]);
    expect(setsOf(".row").get("flex-wrap")).toBe("wrap");
    // The field is as high as the buttons beside it, whatever a pixel of their drawing is.
    expect(setsOf(".row").get("align-items")).toBe("stretch");
  });

  test("test_every_colour_is_a_token_and_no_picture_is_named_by_the_style_sheet", () => {
    expect(CSS.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).toEqual([]);
    expect(CSS.match(/url\(/g) ?? []).toEqual([]);
    // It asks the width of its own box and never that of the screen.
    expect(rulesOf(CSS).filter((rule) => /@media[^{]*\b(width|height)\b/.test(rule.under ?? ""))).toEqual([]);
  });
});
