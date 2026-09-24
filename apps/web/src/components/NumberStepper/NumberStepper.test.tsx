import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { faultsIn } from "../../../test/support/axe";
import { NumberStepper } from "./NumberStepper";

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
