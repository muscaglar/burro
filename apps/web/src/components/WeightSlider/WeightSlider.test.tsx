import { readFileSync } from "node:fs";
import path from "node:path";

import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SLIDER } from "@/content/settings";
import { recordedAnswer } from "@/lib/api/recorded";
import { VIBE_BANDS } from "@/lib/vibes";

import { faultsIn } from "../../../test/support/axe";
import { heavier, rulesOf, subjectOf, weightOf } from "../../../test/support/css";
import { cutOf, sizeOf } from "../kit/drawings";
import { ENDS, NO_PICTURE, pictureAtEnd, picturesAtEnds } from "../kit/Ends/picture";
import { STEPS } from "../kit/Gauge/filled";
import { drawingOf, outlineOf, PLAIN } from "../kit/Thing/drawn";
import { ENDS_OF_ONE_WAY, ENDS_OF_ONE_WAY_MAY_BE } from "./look";
import { eachWay, stepsOf } from "./steps";
import { SETTLE_MS, SliderAtRest, towardsInWords, WeightSlider } from "./WeightSlider";

const meta = recordedAnswer("get_meta", "meta").body.data;
const { limits } = meta;
const LABEL = "How much it counts";

const CSS = readFileSync(path.join(__dirname, "WeightSlider.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const ALL = rulesOf(CSS);
const STYLES = ALL.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
/** What the style sheet sets of a selector, wherever it holds, with every gap in a value made one. */
const setsOf = (selector: string) =>
  new Map(
    STYLES.filter((rule) => rule.selector === selector).flatMap((rule) =>
      [...rule.sets].map(([property, value]): [string, string] => [property, value.replace(/\s+/g, " ")]),
    ),
  );

function show(value = 0.5, version = 1) {
  const onCommit = jest.fn();
  const view = render(
    <WeightSlider value={value} limits={limits} label={LABEL} onCommit={onCommit} version={version} />,
  );
  const again = (next: number, nextVersion: number) =>
    view.rerender(
      <WeightSlider value={next} limits={limits} label={LABEL} onCommit={onCommit} version={nextVersion} />,
    );
  return { onCommit, again, ...view };
}

const slider = () => screen.getByRole("slider", { name: LABEL });
const field = () => screen.getByRole("textbox", { name: SLIDER.number(LABEL) });

afterEach(() => jest.useRealTimers());

describe("the slider", () => {
  test("test_dragging_sends_nothing_until_the_pointer_is_released_and_then_sends_once", () => {
    jest.useFakeTimers();
    const { onCommit } = show(0.5);

    fireEvent.pointerDown(slider());
    for (const value of [55, 60, 65, 70, 75, 80]) {
      fireEvent.change(slider(), { target: { value: String(value) } });
      act(() => void jest.advanceTimersByTime(SETTLE_MS * 2));
    }
    // It shows where it is while it is dragged, and has sent nothing.
    expect(slider()).toHaveValue("80");
    expect(field()).toHaveValue("80");
    expect(onCommit).not.toHaveBeenCalled();

    fireEvent.pointerUp(slider());

    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(onCommit).toHaveBeenCalledWith(0.8);
    act(() => void jest.advanceTimersByTime(SETTLE_MS * 2));
    expect(onCommit).toHaveBeenCalledTimes(1);
  });

  test("test_a_drag_that_ends_off_the_slider_is_still_sent_once", () => {
    const { onCommit } = show(0.5);

    fireEvent.pointerDown(slider());
    fireEvent.change(slider(), { target: { value: "30" } });
    fireEvent.pointerCancel(slider());

    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(onCommit).toHaveBeenCalledWith(0.3);
  });

  test("test_the_arrow_keys_send_once_a_moment_after_the_last_key", () => {
    jest.useFakeTimers();
    const { onCommit } = show(0.5);

    for (const value of [55, 60, 65]) {
      fireEvent.change(slider(), { target: { value: String(value) } });
      act(() => void jest.advanceTimersByTime(SETTLE_MS - 1));
    }
    expect(onCommit).not.toHaveBeenCalled();
    act(() => void jest.advanceTimersByTime(1));

    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(onCommit).toHaveBeenCalledWith(0.65);
  });

  test("test_the_buttons_move_it_by_a_small_step_and_send_once_after_the_last_press", () => {
    jest.useFakeTimers();
    const { onCommit } = show(0.5);

    fireEvent.click(screen.getByRole("button", { name: SLIDER.more(LABEL) }));
    fireEvent.click(screen.getByRole("button", { name: SLIDER.more(LABEL) }));
    fireEvent.click(screen.getByRole("button", { name: SLIDER.less(LABEL) }));
    expect(slider()).toHaveValue("60");
    expect(onCommit).not.toHaveBeenCalled();
    act(() => void jest.advanceTimersByTime(SETTLE_MS));

    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(onCommit).toHaveBeenCalledWith(0.6);
  });

  test("test_the_buttons_stop_at_the_ends", () => {
    show(0.95);

    fireEvent.click(screen.getByRole("button", { name: SLIDER.more(LABEL) }));

    expect(slider()).toHaveValue("100");
    expect(screen.getByRole("button", { name: SLIDER.more(LABEL) })).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByRole("button", { name: SLIDER.less(LABEL) })).not.toHaveAttribute("aria-disabled");
  });

  test("test_a_button_that_is_pressed_to_the_end_keeps_the_focus_and_then_does_nothing", async () => {
    // Seen in a browser, of another button: one that is switched off while it has the focus
    // leaves the focus on nothing. A button pressed until the slider is at its end says
    // that it is off, and is not switched off.
    jest.useFakeTimers();
    const { onCommit } = show(0.05);
    const less = screen.getByRole("button", { name: SLIDER.less(LABEL) });
    less.focus();

    fireEvent.click(less);
    fireEvent.click(less);
    fireEvent.click(less);
    act(() => void jest.advanceTimersByTime(SETTLE_MS * 2));

    expect(slider()).toHaveValue("0");
    expect(less).not.toBeDisabled();
    expect(less).toHaveAttribute("aria-disabled", "true");
    expect(less).toHaveFocus();
    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(onCommit).toHaveBeenCalledWith(0);
  });

  test("test_a_typed_number_is_sent_when_the_field_is_left_and_is_kept_to_a_step_the_api_takes", async () => {
    const user = userEvent.setup({ delay: null });
    const { onCommit } = show(0.5);

    await user.clear(field());
    await user.type(field(), "7");
    expect(onCommit).not.toHaveBeenCalled();
    await user.type(field(), "3");
    await user.tab();

    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(onCommit).toHaveBeenCalledWith(0.75);
    expect(field()).toHaveValue("75");
  });

  test.each([
    ["500", 1],
    ["-4", 0],
  ])("test_a_typed_number_outside_the_range_is_brought_within_it: %s", async (typed, sent) => {
    const user = userEvent.setup({ delay: null });
    const { onCommit } = show(0.5);

    await user.clear(field());
    await user.type(field(), `${typed}{Enter}`);

    expect(onCommit).toHaveBeenCalledWith(sent);
  });

  test("test_what_is_no_number_is_not_sent_and_the_field_goes_back", async () => {
    const user = userEvent.setup({ delay: null });
    const { onCommit } = show(0.5);

    await user.clear(field());
    await user.type(field(), "lots{Enter}");

    expect(onCommit).not.toHaveBeenCalled();
    expect(field()).toHaveValue("50");
  });

  test("test_a_value_that_did_not_change_is_not_sent", () => {
    const { onCommit } = show(0.5);

    fireEvent.pointerDown(slider());
    fireEvent.change(slider(), { target: { value: "70" } });
    fireEvent.change(slider(), { target: { value: "50" } });
    fireEvent.pointerUp(slider());

    expect(onCommit).not.toHaveBeenCalled();
  });

  test("test_the_slider_is_drawn_again_from_every_answer_even_one_that_refused_the_change", () => {
    const { again } = show(0.5, 1);

    fireEvent.pointerDown(slider());
    fireEvent.change(slider(), { target: { value: "90" } });
    fireEvent.pointerUp(slider());
    expect(slider()).toHaveValue("90");

    // The answer came back, and the weight is what it was: the change was refused.
    again(0.5, 2);
    expect(slider()).toHaveValue("50");
    expect(field()).toHaveValue("50");
  });

  test("test_an_answer_that_comes_while_it_is_dragged_does_not_pull_it_from_the_hand", () => {
    const { again } = show(0.5, 1);

    fireEvent.pointerDown(slider());
    fireEvent.change(slider(), { target: { value: "90" } });
    again(0.6, 2);
    expect(slider()).toHaveValue("90");

    // On release it stays where it was put, until the answer to that comes.
    fireEvent.pointerUp(slider());
    expect(slider()).toHaveValue("90");
    again(0.85, 3);
    expect(slider()).toHaveValue("85");
  });

  test("test_a_value_put_back_before_the_answer_comes_is_sent_so_that_the_one_waiting_is_undone", async () => {
    const user = userEvent.setup({ delay: null });
    const { onCommit } = show(0.5);

    await user.clear(field());
    await user.type(field(), "70{Enter}");
    // No answer has come, and 70 is on its way. The person puts it back to 50.
    await user.clear(field());
    await user.type(field(), "50{Enter}");

    expect(onCommit.mock.calls).toEqual([[0.7], [0.5]]);
    expect(slider()).toHaveValue("50");
  });

  test("test_the_same_value_set_twice_before_the_answer_comes_is_sent_once", async () => {
    const user = userEvent.setup({ delay: null });
    const { onCommit } = show(0.5);

    await user.clear(field());
    await user.type(field(), "70{Enter}");
    fireEvent.pointerDown(slider());
    fireEvent.change(slider(), { target: { value: "70" } });
    fireEvent.pointerUp(slider());

    expect(onCommit.mock.calls).toEqual([[0.7]]);
  });

  test("test_after_the_answer_a_value_is_held_against_what_the_answer_said", async () => {
    const user = userEvent.setup({ delay: null });
    const { onCommit, again } = show(0.5, 1);

    await user.clear(field());
    await user.type(field(), "70{Enter}");
    // The answer refused it: the weight is what it was.
    again(0.5, 2);
    await user.clear(field());
    await user.type(field(), "50{Enter}");

    expect(onCommit.mock.calls).toEqual([[0.7]]);
  });

  test("test_an_answer_that_comes_before_a_change_is_sent_does_not_take_the_change_away", () => {
    jest.useFakeTimers();
    const { onCommit, again } = show(0.5, 1);

    fireEvent.click(screen.getByRole("button", { name: SLIDER.more(LABEL) }));
    expect(slider()).toHaveValue("60");
    // An answer to something else comes in the moment before the press is sent.
    again(0.55, 2);
    expect(slider()).toHaveValue("60");
    act(() => void jest.advanceTimersByTime(SETTLE_MS));

    expect(onCommit.mock.calls).toEqual([[0.6]]);
    // It stays where it was put until the answer to that comes.
    expect(slider()).toHaveValue("60");
    again(0.6, 3);
    expect(slider()).toHaveValue("60");
    again(0.65, 4);
    expect(slider()).toHaveValue("65");
  });

  test("test_an_answer_that_arrives_while_a_number_is_typed_leaves_the_typing_alone", async () => {
    const user = userEvent.setup({ delay: null });
    const { onCommit, again } = show(0.5, 1);

    await user.clear(field());
    await user.type(field(), "7");
    again(0.3, 2);
    expect(field()).toHaveValue("7");
    await user.type(field(), "5{Enter}");

    expect(onCommit.mock.calls).toEqual([[0.75]]);
  });

  test("test_a_slider_nobody_has_moved_is_drawn_from_the_spec_whenever_the_spec_changes", () => {
    const { again } = show(0.5, 1);

    // A spec may change with no answer counted, as when a reading comes while an edit waits.
    again(0.7, 1);

    expect(slider()).toHaveValue("70");
    expect(field()).toHaveValue("70");
  });

  test("test_it_moves_in_the_steps_the_api_serves", () => {
    show(0.5);

    expect(slider()).toHaveAttribute("step", String(limits.weight_unit * 100));
    expect(slider()).toHaveAttribute("min", "0");
    expect(slider()).toHaveAttribute("max", "100");
  });

  test("test_what_the_scale_means_is_drawn_where_it_can_be_seen", () => {
    // Seen in a browser: the line that says what 0 and 100 mean was 1 pixel by 1, kept for a
    // screen reader alone. It explains the control, so it is for everyone.
    show(0.5);

    const scale = screen.getByText(SLIDER.range);
    expect(scale.closest(".visually-hidden, [aria-hidden='true'], [hidden]")).toBeNull();
    expect(slider()).toHaveAccessibleDescription(SLIDER.range);
    expect(field()).toHaveAccessibleDescription(SLIDER.range);
  });

  test("test_a_slider_in_a_group_that_gives_the_scale_once_is_described_by_that_line_and_draws_none", () => {
    render(
      <div>
        <p id="scale-of-the-group">{SLIDER.range}</p>
        <WeightSlider
          value={0.5}
          limits={limits}
          label={LABEL}
          onCommit={jest.fn()}
          version={1}
          scale="scale-of-the-group"
        />
      </div>,
    );

    expect(screen.getAllByText(SLIDER.range)).toHaveLength(1);
    expect(slider()).toHaveAccessibleDescription(SLIDER.range);
  });

  test("test_the_slider_has_no_accessibility_fault", async () => {
    const { container } = show(0.5);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("a slider with two named ends", () => {
  const ENDS = ["Calm", "Buzzy"] as const;

  function showScale(value = 0, version = 1) {
    const onCommit = jest.fn();
    const draw = (shown: number, at: number) => (
      <WeightSlider value={shown} limits={limits} label="Going out" onCommit={onCommit} version={at} ends={ENDS} />
    );
    const view = render(draw(value, version));
    return { onCommit, again: (next: number, at: number) => view.rerender(draw(next, at)), ...view };
  }
  const scale = () => screen.getByRole("slider", { name: "Going out" });

  test("test_it_rests_in_the_middle_which_is_no_weight_and_runs_to_either_end", () => {
    showScale(0);

    expect(scale()).toHaveAttribute("min", "-100");
    expect(scale()).toHaveAttribute("max", "100");
    expect(scale()).toHaveValue("0");
    expect(scale()).toHaveAttribute("aria-valuetext", SLIDER.middle);
    expect(screen.getByRole("status")).toHaveTextContent(SLIDER.middle);
  });

  test("test_where_it_stands_is_said_in_words_with_the_name_of_the_end", () => {
    const { again } = showScale(-0.5);
    expect(towardsInWords(-50, ENDS)).toBe(SLIDER.towards("Calm", 50));
    expect(scale()).toHaveAttribute("aria-valuetext", SLIDER.towards("Calm", 50));

    again(0.75, 2);

    expect(scale()).toHaveValue("75");
    expect(screen.getByRole("status")).toHaveTextContent(SLIDER.towards("Buzzy", 75));
  });

  test("test_it_sends_once_on_release_with_the_sign_of_the_end_it_is_towards", () => {
    const { onCommit } = showScale(0);

    fireEvent.pointerDown(scale());
    fireEvent.change(scale(), { target: { value: "-30" } });
    fireEvent.change(scale(), { target: { value: "-60" } });
    expect(onCommit).not.toHaveBeenCalled();
    fireEvent.pointerUp(scale());

    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(onCommit).toHaveBeenCalledWith(-0.6);
  });

  test("test_each_end_is_a_button_that_moves_it_a_step_towards_that_end_with_no_dragging", () => {
    jest.useFakeTimers();
    const { onCommit } = showScale(0);

    fireEvent.click(screen.getByRole("button", { name: SLIDER.toward("Going out", "Calm") }));
    act(() => void jest.advanceTimersByTime(SETTLE_MS));
    expect(onCommit).toHaveBeenLastCalledWith(-limits.weight_step_small);

    fireEvent.click(screen.getByRole("button", { name: SLIDER.toward("Going out", "Buzzy") }));
    fireEvent.click(screen.getByRole("button", { name: SLIDER.toward("Going out", "Buzzy") }));
    act(() => void jest.advanceTimersByTime(SETTLE_MS));
    expect(onCommit).toHaveBeenLastCalledWith(limits.weight_step_small);
  });

  test("test_at_an_end_its_button_says_it_is_off_and_is_not_switched_off", () => {
    showScale(-1);
    const calm = screen.getByRole("button", { name: SLIDER.toward("Going out", "Calm") });

    expect(calm).toHaveAttribute("aria-disabled", "true");
    expect(calm).toBeEnabled();
    expect(screen.getByRole("button", { name: SLIDER.toward("Going out", "Buzzy") })).not.toHaveAttribute("aria-disabled");
  });

  test("test_it_has_no_field_to_type_in_because_a_number_does_not_say_which_end", () => {
    showScale(0.5);

    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.getByText(SLIDER.twoEnds)).toBeVisible();
    expect(scale()).toHaveAccessibleDescription(SLIDER.twoEnds);
  });

  test("test_a_slider_with_two_ends_has_no_accessibility_fault", async () => {
    const { container } = showScale(-0.5);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the slider, drawn as a gauge of steps that fill", () => {
  /** What is drawn under the slider: the gauge of the kit, its steps and its weight. */
  const gaugeOf = (container: HTMLElement) => {
    const holds = container.querySelector(".gauge") as HTMLElement;
    const drawn = holds.firstElementChild as HTMLElement;
    const steps = [...drawn.querySelectorAll<HTMLElement>("[data-full]")];
    return {
      holds,
      drawn,
      steps,
      full: steps.filter((step) => step.dataset.full === "true").length,
      weight: [...drawn.querySelectorAll<HTMLElement>("[style]")].find((one) => /ui-weight/.test(one.style.getPropertyValue("--art"))) as HTMLElement,
      middle: drawn.querySelectorAll(".middle").length,
    };
  };
  const leftOf = (drawn: HTMLElement) => Number(drawn.style.getPropertyValue("--left"));
  /** A vibe of the release that runs one way, and one that is a scale: by what the API says of each, and by no name. */
  const oneWay = meta.tags.find((tag) => tag.shape === "one_way");
  const aScale = meta.tags.find((tag) => tag.shape === "scale" && tag.low_end !== null && tag.high_end !== null);

  test("test_the_gauge_lies_under_the_range_input_which_stays_what_it_is", () => {
    const { container } = show(0.5);
    const { holds, drawn } = gaugeOf(container);

    // What a person moves is the browser's own range input, with its name, its steps and its description.
    expect(slider().tagName).toBe("INPUT");
    expect(slider()).toHaveAttribute("type", "range");
    expect(slider()).toHaveClass("target");
    // The two are held together, the gauge first and the input laid over it.
    expect([...holds.children]).toEqual([drawn, slider()]);
    expect(drawn).toHaveAttribute("data-alone", "false");
    expect([setsOf(".gauge").get("position"), setsOf(".range").get("position"), setsOf(".range").get("inset")]).toEqual([
      "relative",
      "absolute",
      "0",
    ]);
    expect([setsOf(".range").get("width"), setsOf(".range").get("height")]).toEqual(["100%", "100%"]);
  });

  test("test_the_gauge_says_nothing_so_that_the_slider_is_heard_once", () => {
    const { container } = show(0.5);
    const { drawn } = gaugeOf(container);

    expect(drawn.textContent).toBe("");
    expect(drawn.querySelector("button, input, a, [tabindex], [role]")).toBeNull();
    expect(drawn.firstElementChild).toHaveAttribute("aria-hidden", "true");
    expect(screen.getAllByRole("slider")).toHaveLength(1);
    expect(slider()).toHaveAccessibleName(LABEL);
  });

  test("test_the_gauge_follows_the_slider_at_once_while_it_is_dragged_and_before_anything_is_sent", () => {
    const { container, onCommit } = show(0.5);
    const at = () => leftOf(gaugeOf(container).weight);
    const was = at();

    expect(gaugeOf(container).full).toBe(5);
    fireEvent.pointerDown(slider());
    fireEvent.change(slider(), { target: { value: "80" } });

    expect(onCommit).not.toHaveBeenCalled();
    expect(gaugeOf(container).full).toBe(8);
    expect(at()).toBeGreaterThan(was);
    fireEvent.change(slider(), { target: { value: "0" } });
    expect(gaugeOf(container).full).toBe(0);
    expect(at()).toBe(0);
  });

  test("test_a_press_of_the_plus_fills_a_step_and_of_the_minus_empties_one", () => {
    const { container } = show(0.5);

    fireEvent.click(screen.getByRole("button", { name: SLIDER.more(LABEL) }));
    expect(gaugeOf(container).full).toBe(6);
    fireEvent.click(screen.getByRole("button", { name: SLIDER.less(LABEL) }));
    fireEvent.click(screen.getByRole("button", { name: SLIDER.less(LABEL) }));
    expect(gaugeOf(container).full).toBe(4);
  });

  test("test_the_gauge_is_drawn_again_from_every_answer_as_the_slider_is", () => {
    const { container, again } = show(0.5, 1);

    again(0.2, 2);

    expect(slider()).toHaveValue("20");
    expect(gaugeOf(container).full).toBe(2);
  });

  test("test_the_gauge_has_a_step_for_each_press_by_the_small_step_the_api_serves", () => {
    const { container } = show(0.5);
    const small = Math.round(limits.weight_step_small * 100);

    expect(gaugeOf(container).steps).toHaveLength(stepsOf(small));
    expect(stepsOf(small)).toBe(Math.round(100 / small));
  });

  test("test_a_gauge_has_more_steps_than_a_band_has_and_no_more_than_it_has_room_for", () => {
    // It must never be taken for where an area sits on a vibe, which is five steps and a peg.
    for (const small of [1, 2, 5, 10, 12.5, 20, 25, 50, 100, 0, -10, Number.NaN]) {
      expect([small, stepsOf(small) > VIBE_BANDS.length, stepsOf(small) <= STEPS]).toEqual([small, true, true]);
    }
    expect([stepsOf(10), stepsOf(12.5), stepsOf(5), stepsOf(20)]).toEqual([10, 8, STEPS, STEPS]);
    // A scale has half as many each way from its middle, and so as many in all.
    expect([eachWay(10), eachWay(8), eachWay(7), eachWay(1)]).toEqual([5, 4, 4, 1]);
  });

  test("test_the_thumb_of_the_input_is_as_wide_as_the_weight_so_that_the_weight_stands_where_the_thumb_is", () => {
    const { container } = show(0.5);
    const { holds, drawn } = gaugeOf(container);
    const weight = sizeOf("ui-weight");

    expect(holds.style.getPropertyValue("--thumb")).toBe(String(weight.width));
    // And as high as the gauge is drawn, which says its own height in pixels of the drawing.
    expect(holds.style.getPropertyValue("--high")).toBe((drawn.firstElementChild as HTMLElement).style.getPropertyValue("--high"));
    // The gauge is as wide as the travel of such a thumb, and the input is as wide as the gauge.
    const gauge = drawn.firstElementChild as HTMLElement;
    const steps = stepsOf(Math.round(limits.weight_step_small * 100));
    expect(gauge.style.getPropertyValue("--wide")).toBe(String(steps * (sizeOf("gauge-cell").width - 1) + 1 + weight.width));
    // Each browser names the thumb in its own way. A rule that names both is thrown away
    // whole by a browser that knows one, so each is said by itself.
    const thumbs = STYLES.filter((rule) => /::(-webkit-slider-thumb|-moz-range-thumb)$/.test(rule.selector));
    expect(thumbs.map((rule) => rule.selector).sort()).toEqual([".range::-moz-range-thumb", ".range::-webkit-slider-thumb"]);
    for (const rule of thumbs) {
      expect([rule.selector, rule.sets.get("width"), rule.sets.get("height")]).toEqual([
        rule.selector,
        "calc(var(--px) * var(--thumb))",
        "calc(var(--px) * var(--high))",
      ]);
    }
    const written = CSS.replace(/\s+/g, " ");
    expect(/::-webkit-slider-thumb\s*,|,\s*[^{}]*::-webkit-slider-thumb|::-moz-range-thumb\s*,|,\s*[^{}]*::-moz-range-thumb/.test(written)).toBe(false);
  });

  test("test_nothing_of_the_input_is_drawn_but_the_ring_of_its_focus_and_nothing_is_see_through", () => {
    const clear = STYLES.filter((rule) => /^\.range(::|$)/.test(rule.selector));

    expect(clear.map((rule) => [rule.selector, rule.sets.get("background")])).toEqual([
      [".range", "transparent"],
      [".range::-webkit-slider-runnable-track", "transparent"],
      [".range::-webkit-slider-thumb", "transparent"],
      [".range::-moz-range-track", "transparent"],
      [".range::-moz-range-thumb", "transparent"],
    ]);
    expect(setsOf(".range").get("appearance")).toBe("none");
    // It is not faded away: what is faded is still drawn. And the ring of its focus is never taken off.
    expect(STYLES.filter((rule) => [...rule.sets.keys()].some((property) => /^(opacity|filter|visibility)$/.test(property)))).toEqual([]);
    const ringless = ALL.filter((rule) =>
      ["outline", "outline-style", "outline-width"].some((property) => /^(none|0)\b/.test(rule.sets.get(property) ?? "")),
    );
    expect(ringless.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_a_scale_has_two_runs_of_steps_and_fills_from_its_middle_towards_the_end_it_is_moved_to", () => {
    const ends = [aScale?.low_end ?? "", aScale?.high_end ?? ""] as const;
    const { container, rerender } = render(
      <WeightSlider value={-0.6} limits={limits} label={aScale?.label ?? ""} onCommit={jest.fn()} version={1} ends={ends} />,
    );
    const each = eachWay(stepsOf(Math.round(limits.weight_step_small * 100)));
    const filled = () => gaugeOf(container).steps.map((step) => step.dataset.full === "true");

    expect(aScale).toBeDefined();
    expect(gaugeOf(container).steps).toHaveLength(each * 2);
    expect(gaugeOf(container).middle).toBe(1);
    // Towards the low end it fills from the middle leftwards, and the high run stays empty.
    expect(filled().slice(each)).toEqual(Array(each).fill(false));
    expect(filled().slice(0, each).filter(Boolean).length).toBeGreaterThan(0);
    expect(filled().slice(0, each).lastIndexOf(true)).toBe(each - 1);

    rerender(<WeightSlider value={0} limits={limits} label={aScale?.label ?? ""} onCommit={jest.fn()} version={2} ends={ends} />);
    expect(filled()).toEqual(Array(each * 2).fill(false));
  });

  /** The picture a button of a slider bears, by where it is served from. `undefined` of a button that bears a sign. */
  const pictureOn = (button: HTMLElement) =>
    button.querySelector<HTMLElement>("[style*='--art:']:not(.face)")?.style.getPropertyValue("--art");
  const served = (name: string) => `url("/art/${name}.png")`;

  test("test_each_end_of_a_scale_is_a_button_that_holds_the_one_picture_of_that_end_of_its_vibe_and_its_name", () => {
    const ends = [aScale?.low_end ?? "", aScale?.high_end ?? ""] as const;
    const label = aScale?.label ?? "";
    const vibe = aScale?.tag_id ?? "";
    render(<WeightSlider value={0} limits={limits} label={label} onCommit={jest.fn()} version={1} ends={ends} vibe={vibe} />);

    for (const [at, end] of ends.entries()) {
      const button = screen.getByRole("button", { name: SLIDER.toward(label, end) });
      const picture = button.querySelector<HTMLElement>("[style*='--art:']:not(.face)");
      expect(button.tagName).toBe("BUTTON");
      expect(button).toHaveClass("target");
      // What is seen on it is its picture and the name of its end, as the API names it.
      expect(button).toHaveTextContent(new RegExp(`^${end}$`));
      // The picture is chosen by the id the API gives the vibe, and is dress: it says nothing.
      expect(pictureOn(button)).toBe(served(pictureAtEnd(vibe, ENDS[at] ?? "low")));
      expect(picture).toHaveAttribute("aria-hidden", "true");
      expect(pictureAtEnd(vibe, ENDS[at] ?? "low")).not.toBe(NO_PICTURE);
    }
    // The two are opposites: no vibe has one picture at both its ends.
    const [low, high] = picturesAtEnds(vibe);
    expect(low === high).toBe(false);
  });

  test("test_a_scale_whose_ends_nobody_has_drawn_takes_the_blank_picture_at_both_and_keeps_their_names", () => {
    const ends = ["Inland", "By the water"] as const;
    const drawn = (vibe: string | undefined) => {
      const { unmount } = render(
        <WeightSlider value={0} limits={limits} label="Where" onCommit={jest.fn()} version={1} ends={ends} vibe={vibe} />,
      );
      const found = ends.map((end) => {
        const button = screen.getByRole("button", { name: SLIDER.toward("Where", end) });
        return [pictureOn(button), button.textContent];
      });
      unmount();
      return found;
    };

    // A vibe that is new to the website, and a slider that is told of no vibe at all.
    for (const vibe of ["a_vibe_nobody_drew", undefined]) {
      expect(drawn(vibe)).toEqual(ends.map((end) => [served(NO_PICTURE), end]));
    }
  });

  test("test_the_two_buttons_of_the_slider_of_a_vibe_that_runs_one_way_bear_the_picture_of_each_end_of_the_vibe", () => {
    const label = oneWay?.label ?? "";
    const vibe = oneWay?.tag_id ?? "";
    const onCommit = jest.fn();
    jest.useFakeTimers();
    render(<WeightSlider value={0.5} limits={limits} label={label} onCommit={onCommit} version={1} vibe={vibe} oneWay="pictured" />);
    const [less, more] = [SLIDER.less(label), SLIDER.more(label)].map((name) => screen.getByRole("button", { name }));
    if (less === undefined || more === undefined) throw new Error("The slider has no two buttons.");

    expect(oneWay).toBeDefined();
    // What there is little of at its low end, and what there is much of at its high end: the
    // two are opposites, and are the pictures the gauge of a result has at its ends.
    expect([pictureOn(less), pictureOn(more)]).toEqual(picturesAtEnds(vibe).map(served));
    expect(pictureOn(less) === pictureOn(more)).toBe(false);
    for (const button of [less, more]) {
      // Each is a button of the look, which says what it does to whoever hears the page.
      expect(button.tagName).toBe("BUTTON");
      expect(button).toHaveClass("target");
      expect(button.firstElementChild).toHaveClass("face");
      // The picture is dress, and no word stands on the button: its name says what it does.
      expect(button.textContent).toBe("");
      expect(button.querySelector("[style*='--art:']:not(.face)")).toHaveAttribute("aria-hidden", "true");
    }
    // Each does what it did: a press moves the slider a small step.
    fireEvent.click(more);
    fireEvent.click(more);
    fireEvent.click(less);
    act(() => void jest.advanceTimersByTime(SETTLE_MS));
    expect(screen.getByRole("slider", { name: label })).toHaveValue("60");
    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(onCommit).toHaveBeenCalledWith(0.6);
  });

  test("test_every_vibe_of_the_release_that_runs_one_way_has_a_picture_for_each_button_of_its_slider", () => {
    const blank = meta.tags.filter((tag) => tag.shape === "one_way" && picturesAtEnds(tag.tag_id).includes(NO_PICTURE));

    expect(blank.map((tag) => tag.tag_id)).toEqual([]);
  });

  test("test_by_one_line_the_two_buttons_bear_a_minus_and_a_plus_as_they_did", () => {
    const label = oneWay?.label ?? "";
    render(
      <WeightSlider value={0.5} limits={limits} label={label} onCommit={jest.fn()} version={1} vibe={oneWay?.tag_id ?? ""} oneWay="signs" />,
    );

    const drawn = [SLIDER.less(label), SLIDER.more(label)].map((name) => screen.getByRole("button", { name }).style.getPropertyValue("--art"));

    expect(drawn).toEqual([served("btn-less"), served("btn-more")]);
    expect(ENDS_OF_ONE_WAY_MAY_BE).toEqual(["pictured", "signs"]);
    expect(ENDS_OF_ONE_WAY_MAY_BE).toContain(ENDS_OF_ONE_WAY);
  });

  test("test_a_slider_of_no_vibe_and_of_a_vibe_nobody_has_drawn_keeps_its_minus_and_its_plus", () => {
    // How much a measurement counts, or the budget, is the slider of no vibe: nothing is
    // drawn of two ends it has not got. And a plot with nothing on it at both ends would
    // say nothing of what a press does.
    for (const vibe of [undefined, null, "a_vibe_nobody_drew"]) {
      const { unmount } = render(
        <WeightSlider value={0.5} limits={limits} label={LABEL} onCommit={jest.fn()} version={1} vibe={vibe} oneWay="pictured" />,
      );
      const drawn = [SLIDER.less(LABEL), SLIDER.more(LABEL)].map((name) => screen.getByRole("button", { name }).style.getPropertyValue("--art"));
      expect([vibe, drawn]).toEqual([vibe, [served("btn-less"), served("btn-more")]]);
      unmount();
    }
  });

  test("test_the_pictured_buttons_of_a_slider_that_runs_one_way_are_read_where_the_minus_and_the_plus_were", () => {
    const label = oneWay?.label ?? "";
    const { container } = render(
      <WeightSlider value={0.5} limits={limits} label={label} onCommit={jest.fn()} version={1} vibe={oneWay?.tag_id ?? ""} oneWay="pictured" />,
    );
    const read = [...container.querySelectorAll("button, input")].map((one) => one.getAttribute("aria-label") ?? one.getAttribute("type"));

    expect(read).toEqual([SLIDER.less(label), "range", SLIDER.more(label), SLIDER.number(label)]);
    // It is laid out as a slider that runs one way is: its row is not that of two named ends.
    expect(container.querySelector(".row")).toHaveAttribute("data-ends", "false");
  });

  test("test_the_button_of_an_end_is_drawn_as_a_button_is_and_its_face_is_cut_where_its_drawing_says", () => {
    const ends = [aScale?.low_end ?? "", aScale?.high_end ?? ""] as const;
    render(<WeightSlider value={0} limits={limits} label="Of a scale" onCommit={jest.fn()} version={1} ends={ends} />);
    const face = screen.getByRole("button", { name: SLIDER.toward("Of a scale", ends[0]) }).firstElementChild as HTMLElement;
    const handed = (name: string) => face.style.getPropertyValue(name);

    expect(face).toHaveClass("face");
    expect([handed("--art"), handed("--art-down")]).toEqual(['url("/art/ui-button.png")', 'url("/art/ui-button-down.png")']);
    expect(["--cut-top", "--cut-right", "--cut-foot", "--cut-left"].map(handed)).toEqual((cutOf("ui-button") ?? []).map(String));
    // Its picture is laid end to end and never stretched, over a rule of ink and a flat ground.
    expect(setsOf(".face").get("border-image")).toMatch(/^var\(--art\) .+ fill \/ .+ repeat$/);
    expect([setsOf(".face").get("border-color"), setsOf(".face").get("background-color"), setsOf(".face").get("image-rendering")]).toEqual([
      "var(--ink)",
      "var(--page)",
      "pixelated",
    ]);
  });

  test("test_the_picture_of_the_button_of_an_end_pressed_is_asked_for_with_the_page_and_not_at_its_first_press", () => {
    // Seen in a browser, of the button of the kit: asked for at the first press, the
    // picture had not come, and the button was drawn with no edge. It is laid as a ground
    // of no size, which is never seen.
    const face = setsOf(".face");

    expect([face.get("background-image"), face.get("background-size"), face.get("background-repeat")]).toEqual([
      "var(--art-down)",
      "0 0",
      "no-repeat",
    ]);
  });

  test("test_at_an_end_its_button_is_drawn_pressed_and_keeps_its_ink_for_nothing_is_dimmed", () => {
    const off = '.end[aria-disabled="true"]';

    expect(setsOf(`${off} > .face`).get("border-image-source")).toBe("var(--art-down)");
    expect(setsOf(off).get("color")).toBe("var(--ink)");
    // It weighs more than what the page says of every button that is off, which sets it in a quieter colour.
    const base = rulesOf(readFileSync(path.join(__dirname, "..", "..", "styles", "base.css"), "utf8"));
    const ofEveryButton = base.filter((rule) => rule.selector === 'button[aria-disabled="true"]' && rule.sets.has("color"));
    expect(ofEveryButton).toHaveLength(1);
    for (const rule of ofEveryButton) expect(heavier(weightOf(off), weightOf(rule.selector))).toBe(true);
    // Its words stand as they stood: a word that is moved is drawn softer by a browser.
    expect(STYLES.filter((rule) => /aria-disabled/.test(rule.selector) && rule.sets.has("transform"))).toEqual([]);
  });

  test("test_under_a_press_the_picture_changes_and_the_button_neither_moves_nor_changes_size", () => {
    const DRAWN_ONLY = ["background", "background-color", "border-image-source", "color", "cursor"];
    const states = STYLES.filter((rule) => /:(hover|focus|focus-visible|focus-within|active)\b/.test(rule.selector));
    const moved = states.filter((rule) => [...rule.sets.keys()].some((property) => !DRAWN_ONLY.includes(property)));

    expect(states.length).toBeGreaterThan(0);
    // One thing steps: what stands on the face of a button, inside the button, while it is
    // pressed and where the system says that movement is welcome. The button stays.
    expect(moved.map((rule) => [rule.selector, rule.under, [...rule.sets]])).toEqual([
      [".end:active > .face > *", "@media (prefers-reduced-motion: no-preference)", [["transform", "translate(var(--px), var(--px))"]]],
    ]);
    expect(subjectOf(".end:active > .face > *")).toBe("*");
    expect(STYLES.filter((rule) => [...rule.sets.keys()].some((property) => /^(transition|animation)/.test(property)))).toEqual([]);
  });

  test("test_the_thing_that_is_weighed_is_drawn_beside_its_name_by_the_id_the_api_gives_it", () => {
    const thing = { kind: "tag", id: oneWay?.tag_id ?? null, family: oneWay?.family ?? null } as const;
    const label = oneWay?.label ?? "";
    const { container, rerender } = render(
      <WeightSlider value={0.5} limits={limits} label={label} onCommit={jest.fn()} version={1} thing={thing} />,
    );
    const drawnBeside = () => container.querySelector<HTMLElement>("label [aria-hidden='true'] [style]")?.style.getPropertyValue("--art");

    expect(oneWay).toBeDefined();
    expect(drawnBeside()).toBe(`url("/art/${drawingOf(thing)}.png")`);
    // The drawing is dress: the name of the slider is the name the API gives, and no more.
    expect(screen.getByRole("slider")).toHaveAccessibleName(label);
    expect(within(container.querySelector("label") as HTMLElement).getByText(label)).toBeVisible();

    // While it counts for nothing it is drawn in outline, as a chip draws it.
    rerender(<WeightSlider value={0} limits={limits} label={label} onCommit={jest.fn()} version={2} thing={thing} />);
    expect(drawnBeside()).toBe(`url("/art/${outlineOf(drawingOf(thing))}.png")`);
  });

  test("test_a_thing_with_no_drawing_of_its_own_is_drawn_by_its_family_and_then_by_the_plain_one", () => {
    const family = meta.families[0]?.family ?? null;
    const unknown = { kind: "tag", id: "a_vibe_nobody_has_drawn", family } as const;
    const lost = { kind: "tag", id: "a_vibe_nobody_has_drawn", family: "a_family_nobody_has_drawn" } as const;
    const { container, rerender } = render(
      <WeightSlider value={0.5} limits={limits} label="One" onCommit={jest.fn()} version={1} thing={unknown} />,
    );
    const drawnBeside = () => container.querySelector<HTMLElement>("label [aria-hidden='true'] [style]")?.style.getPropertyValue("--art");

    expect(drawnBeside()).toBe(`url("/art/${drawingOf({ kind: "feature", family })}.png")`);
    rerender(<WeightSlider value={0.5} limits={limits} label="One" onCommit={jest.fn()} version={1} thing={lost} />);
    expect(drawnBeside()).toBe(`url("/art/${PLAIN}.png")`);
  });

  test("test_with_no_thing_nothing_is_drawn_beside_the_name", () => {
    const { container } = show(0.5);

    expect(container.querySelector("label [aria-hidden]")).toBeNull();
  });

  test("test_the_name_is_set_in_the_face_of_names_and_every_figure_and_sentence_in_the_reading_face", () => {
    expect([setsOf(".label").get("font"), setsOf(".label").get("font-synthesis")]).toEqual([
      "400 var(--name-1) / 1.1 var(--font-name)",
      "none",
    ]);
    expect(setsOf(".row > .number").get("font")).toBe("700 var(--size-lead) / 1.2 var(--font-say)");
    expect(setsOf(".row > .number").get("font-variant-numeric")).toBe("tabular-nums");
    expect(setsOf(".stands").get("font")).toBe("700 var(--size-small) / 1.3 var(--font-say)");
    expect(setsOf(".named").get("font")).toBe("700 var(--size-small) / 1.1 var(--font-say)");
    // No other rule names a face, and none names the face of names for what is read.
    const faces = STYLES.filter((rule) => /var\(--font-name\)/.test(rule.sets.get("font") ?? rule.sets.get("font-family") ?? ""));
    expect(faces.map((rule) => rule.selector)).toEqual([".label"]);
  });

  test("test_a_name_that_holds_a_figure_is_read_and_is_set_in_the_reading_face", () => {
    const { rerender } = render(<WeightSlider value={0.5} limits={limits} label={LABEL} onCommit={jest.fn()} version={1} />);
    expect(screen.getByText(LABEL)).toHaveAttribute("data-reads", "false");

    rerender(<WeightSlider value={0.5} limits={limits} label="Homes of 3 floors or more" onCommit={jest.fn()} version={1} />);
    expect(screen.getByText("Homes of 3 floors or more")).toHaveAttribute("data-reads", "true");
    expect(screen.getByRole("slider")).toHaveAccessibleName("Homes of 3 floors or more");
    expect(setsOf('.name[data-reads="true"]').get("font")).toBe("700 var(--size-body) / 1.2 var(--font-say)");
  });

  test("test_the_field_weighs_more_than_what_the_page_says_of_every_field", () => {
    // Seen in a browser: a hundred was cut short in its field. The page's own rule for every
    // field outweighed the class of this one, and gave it more room at either hand.
    const own = STYLES.filter((rule) => rule.sets.has("padding") && /\.number$/.test(rule.selector));

    expect(own.map((rule) => [rule.selector, heavier(weightOf(rule.selector), [0, 1, 1])])).toEqual([[".row > .number", true]]);
  });

  test("test_it_is_laid_out_by_the_width_of_its_own_box_and_never_by_that_of_the_screen", () => {
    expect(setsOf(".slider").get("container")).toBe("slider / inline-size");
    expect(ALL.filter((rule) => /@media[^{]*\b(width|height)\b/.test(rule.under ?? "")).map((rule) => rule.selector)).toEqual([]);
    // What does not stand in one line goes under, in the order it is read in.
    expect(setsOf(".row").get("flex-wrap")).toBe("wrap");
    // In a narrow box the two ends of a scale stand over its gauge, and nothing of a slider that runs one way is moved.
    const narrow = ALL.filter((rule) => /@container slider/.test(rule.under ?? ""));
    expect(narrow.length).toBeGreaterThan(0);
    expect(narrow.filter((rule) => !/\[data-ends="true"\]/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_in_a_narrow_box_the_two_ends_of_a_scale_stand_over_its_gauge_side_by_side_and_alike", () => {
    const narrow = ALL.filter((rule) => /@container slider/.test(rule.under ?? ""));
    const set = (selector: string) => new Map(narrow.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

    // Seen in a browser, in the column of the settings: the two buttons and the gauge are 294
    // pixels wide, and the column has 234 to give them. Neither end is the better one, so
    // the two are of one width.
    expect(set('.row[data-ends="true"]').get("grid-template-columns")).toBe("minmax(0, 1fr) minmax(0, 1fr)");
    expect([set('.row[data-ends="true"] > .gauge').get("grid-column"), set('.row[data-ends="true"] > .gauge').get("justify-self")]).toEqual([
      "1 / -1",
      "center",
    ]);
    // The gauge is under them and what it says under the gauge: the order they are read in is as it was.
    expect([set('.row[data-ends="true"] > .gauge').get("grid-row"), set('.row[data-ends="true"] > .stands').get("grid-row")]).toEqual(["2", "3"]);
    // Seen in a browser, with the text twice as large: the name of an end was wider than its
    // picture, the three no longer stood in one line, and the high end went under the low
    // one. So how narrow a box must be is asked in the size of the text as well.
    expect([...new Set(narrow.map((rule) => rule.under))]).toEqual(["@container slider (max-width: calc(164px + 2 * max(32px, 4.1rem)))"]);
    // The 32 is the picture of an end, and the 164 the gauge and the edges of the two buttons, at the pixel of a phone.
    const [picture, gauge, edge] = [sizeOf(pictureAtEnd(aScale?.tag_id, "low")), sizeOf("gauge-cell"), cutOf("ui-button") ?? [0, 0, 0, 0]];
    const each = eachWay(stepsOf(Math.round(limits.weight_step_small * 100)));
    const wide = (each * (gauge.width - 1) + 1) * 2 + 5 + sizeOf("ui-weight").width;
    expect(picture.width * 2).toBe(32);
    expect(wide * 2 + 2 * (edge[1] + edge[3]) * 2 + 2 * 1 * 2).toBeLessThanOrEqual(164 + 2);
  });

  test("test_the_low_end_the_slider_the_high_end_and_where_it_stands_are_read_in_that_order", () => {
    const ends = [aScale?.low_end ?? "", aScale?.high_end ?? ""] as const;
    const { container } = render(
      <WeightSlider value={0} limits={limits} label="Of a scale" onCommit={jest.fn()} version={1} ends={ends} />,
    );
    const read = [...container.querySelectorAll("button, input, output")].map(
      (one) => one.getAttribute("aria-label") ?? one.getAttribute("type") ?? one.tagName.toLowerCase(),
    );

    expect(read).toEqual([SLIDER.toward("Of a scale", ends[0]), "range", SLIDER.toward("Of a scale", ends[1]), "output"]);
  });

  test("test_the_minus_the_slider_the_plus_and_the_field_are_read_in_that_order", () => {
    const { container } = show(0.5);
    const read = [...container.querySelectorAll("button, input")].map((one) => one.getAttribute("aria-label") ?? one.getAttribute("type"));

    expect(read).toEqual([SLIDER.less(LABEL), "range", SLIDER.more(LABEL), SLIDER.number(LABEL)]);
  });

  test("test_every_colour_is_a_token_and_no_picture_is_named_by_the_style_sheet", () => {
    expect(CSS.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).toEqual([]);
    expect(CSS.match(/url\(/g) ?? []).toEqual([]);
  });

  test("test_with_forced_colours_no_picture_is_drawn_over_the_edge_of_a_button", () => {
    const forced = ALL.filter((rule) => /forced-colors/.test(rule.under ?? ""));

    expect(forced.filter((rule) => rule.sets.has("border-image-source")).map((rule) => [rule.selector, rule.sets.get("border-image-source")])).toEqual([
      [".face", "none"],
      [".end:active > .face", "none"],
      ['.end[aria-disabled="true"] > .face', "none"],
    ]);
    // Taken away by its source: said as the whole of the picture, the build makes nothing of it.
    expect(ALL.filter((rule) => (rule.sets.get("border-image") ?? "").trim() === "none")).toEqual([]);
  });
});

describe("the slider of a thing that is switched off, at rest", () => {
  /** How a part is made, by the class of each thing in it, in the order they stand: what a style sheet lays out. */
  const madeAs = (part: Element): string[] =>
    [...part.children].flatMap((one) => [`.${one.classList[0] ?? ""}`, ...madeAs(one).map((inside) => `  ${inside}`)]);
  /** What is laid out of a slider: all of it but the range input, which lies over its gauge and takes no room. */
  const laidOut = (part: Element) => madeAs(part).filter((line) => line.trim() !== ".range");

  test("test_it_is_made_as_the_slider_is_made_so_that_it_keeps_the_room_of_the_slider", () => {
    // Seen in a browser at 390 by 844: a slider drawn as its thing was turned on put what
    // stood under it 80 px down the page.
    const moving = render(<WeightSlider value={0} limits={limits} label={LABEL} onCommit={jest.fn()} version={1} scale="said-once" />);
    const live = laidOut(moving.container);
    moving.unmount();
    const { container } = render(<SliderAtRest limits={limits} label={LABEL} scale="said-once" />);

    expect(laidOut(container)).toEqual(live);
    expect(live.slice(0, 2)).toEqual([".slider", "  .label"]);
    // Its gauge has the steps of the slider, all of them empty, and its weight stands at nought.
    const steps = [...container.querySelectorAll<HTMLElement>("[data-full]")];
    expect(steps).toHaveLength(stepsOf(Math.round(limits.weight_step_small * 100)));
    expect(steps.filter((step) => step.dataset.full === "true")).toEqual([]);
    expect(container.querySelector(".number")).toHaveTextContent(/^0$/);
    expect(container.querySelector(".label")).toHaveTextContent(LABEL);
  });

  test("test_where_the_slider_says_what_its_scale_means_under_itself_so_does_it", () => {
    const moving = render(<WeightSlider value={0} limits={limits} label={LABEL} onCommit={jest.fn()} version={1} />);
    const live = laidOut(moving.container);
    moving.unmount();
    const { container } = render(<SliderAtRest limits={limits} label={LABEL} />);

    expect(laidOut(container)).toEqual(live);
    expect(live.at(-1)).toBe("  .scale");
    expect(container.querySelector(".scale")).toHaveTextContent(SLIDER.range);
  });

  test("test_it_is_a_drawing_which_offers_nothing_and_says_nothing_to_whoever_hears_the_page", () => {
    const { container } = render(<SliderAtRest limits={limits} label={LABEL} />);
    const rests = container.firstElementChild as HTMLElement;

    expect(rests).toHaveAttribute("aria-hidden", "true");
    expect(rests).toHaveAttribute("data-rests");
    for (const role of ["slider", "textbox", "button"] as const) expect(screen.queryAllByRole(role)).toEqual([]);
    // No field and no slider is in it. Its two buttons are switched off, and no keyboard stops on them.
    expect(container.querySelectorAll("input, select, textarea, a, [tabindex]")).toHaveLength(0);
    const buttons = [...container.querySelectorAll("button")];
    expect(buttons.map((button) => [button.disabled, button.getAttribute("aria-label")])).toEqual([
      [true, SLIDER.less(LABEL)],
      [true, SLIDER.more(LABEL)],
    ]);
    expect(container.querySelector("label")).toBeNull();
  });

  test("test_its_figure_stands_as_the_field_of_a_slider_stands", () => {
    const { container } = render(<SliderAtRest limits={limits} label={LABEL} />);
    const figure = container.querySelector(".number") as HTMLElement;

    // It is drawn by what draws the field: as wide, with its edge, its ground and its face.
    expect([figure.tagName, [...figure.classList]]).toEqual(["SPAN", ["number", "rests"]]);
    expect([setsOf(".row > .rests").get("display"), setsOf(".row > .rests").get("align-content"), setsOf(".row > .rests").get("min-block-size")]).toEqual([
      "grid",
      "center",
      "var(--target)",
    ]);
  });

  test("test_at_rest_its_words_are_quieter_in_the_colour_the_look_has_for_that_and_nothing_is_dimmed", () => {
    // A button that does nothing just now has its words in the same colour, on every page.
    expect(setsOf(".slider[data-rests]").get("color")).toBe("var(--muted)");
    expect(setsOf(".row > .rests").get("color")).toBe("inherit");
    // The rule of its figure comes after the rule of a field, which sets ink, and weighs as much.
    const order = STYLES.filter((rule) => /^\.row > \.(number|rests)$/.test(rule.selector) && rule.sets.has("color")).map((rule) => rule.selector);
    expect(order).toEqual([".row > .number", ".row > .rests"]);
    expect(weightOf(".row > .rests")).toEqual(weightOf(".row > .number"));
    // Nothing is see-through: a colour that is dimmed is not the colour whose contrast was checked.
    expect(ALL.filter((rule) => [...rule.sets.keys()].some((property) => /^(opacity|filter|visibility)$/.test(property)))).toEqual([]);
  });

  test("test_what_is_seen_of_the_name_of_a_slider_may_be_the_start_of_it_and_the_whole_is_what_is_heard", () => {
    // Under the name of a thing, the name of its slider said the name of the thing again.
    const whole = `${LABEL}: Nearer a park`;
    const moving = render(<WeightSlider value={0.5} limits={limits} label={whole} seen={LABEL} onCommit={jest.fn()} version={1} />);

    // The whole of its name is what is heard, word for word, of the slider, its buttons and its field.
    expect(screen.getByRole("slider", { name: whole })).toHaveValue("50");
    expect(screen.getByRole("slider")).toHaveAccessibleName(whole);
    expect(screen.getByRole("textbox", { name: SLIDER.number(whole) })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: SLIDER.more(whole) })).toBeInTheDocument();
    // What is seen is the start of it, which is in what is heard: whoever says what they see is understood.
    expect(moving.container.querySelector(".name")?.textContent).toBe(LABEL);
    expect(moving.container.querySelector("label")?.textContent).toBe(LABEL);
    expect(whole.startsWith(LABEL)).toBe(true);
    const live = laidOut(moving.container);
    moving.unmount();

    // At rest it is made alike, so that it is as high: what is seen of its name is the same.
    const { container } = render(<SliderAtRest limits={limits} label={whole} seen={LABEL} />);
    expect(laidOut(container)).toEqual(live);
    expect(container.querySelector(".name")?.textContent).toBe(LABEL);
  });

  test("test_a_name_that_does_not_begin_with_what_is_to_be_seen_of_it_is_seen_whole", () => {
    const { container } = render(<WeightSlider value={0.5} limits={limits} label={LABEL} seen="Another thing" onCommit={jest.fn()} version={1} />);

    expect(screen.getByRole("slider", { name: LABEL })).not.toHaveAttribute("aria-label");
    expect(container.querySelector(".name")?.textContent).toBe(LABEL);
  });

  test("test_a_slider_whose_name_is_seen_whole_is_named_by_what_is_seen_and_by_nothing_else", () => {
    show(0.5);

    expect(slider()).not.toHaveAttribute("aria-label");
    expect(slider()).toHaveAccessibleName(LABEL);
  });

  test("test_at_rest_it_has_no_accessibility_fault", async () => {
    const { container } = render(<SliderAtRest limits={limits} label={LABEL} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
