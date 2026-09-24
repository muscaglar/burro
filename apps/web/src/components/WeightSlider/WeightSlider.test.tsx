import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SLIDER } from "@/content/settings";
import { recordedAnswer } from "@/lib/api/recorded";

import { faultsIn } from "../../../test/support/axe";
import { SETTLE_MS, WeightSlider } from "./WeightSlider";

const { limits } = recordedAnswer("get_meta", "meta").body.data;
const LABEL = "How much it counts";

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
