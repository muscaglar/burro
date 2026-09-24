import { readFileSync } from "node:fs";
import path from "node:path";

import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";

import { EXAMPLES, PROMPT } from "@/content/search";
import { READER, WORDS_LINE } from "@/content/site";
import { recordedAnswer } from "@/lib/api/recorded";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { Examples, PromptBox, type PromptHandle } from "./PromptBox";

function show(props: Partial<Parameters<typeof PromptBox>[0]> = {}) {
  const onSubmit = jest.fn();
  const onStop = jest.fn();
  const handle = createRef<PromptHandle>();
  const view = render(
    <PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} ref={handle} {...props} />,
  );
  return { onSubmit, onStop, handle, user: userEvent.setup({ delay: null }), ...view };
}

const box = () => screen.getByRole<HTMLTextAreaElement>("textbox", { name: /./ });

// What the service says of who reads, as it was recorded: where the rules read, where a
// model does, and where the search settings are sent with the words.
const byRules = recordedAnswer("get_meta", "meta").body.data.reader;
const byAModel = recordedAnswer("get_meta", "meta-model-reads").body.data.reader;
const withSettings = recordedAnswer("get_meta", "meta-model-reads-with-settings").body.data.reader;

/** The box with the examples beside it, wired as the page wires them. */
function showWithExamples(props: Partial<Parameters<typeof PromptBox>[0]> = {}) {
  const onSubmit = jest.fn();
  const handle = createRef<PromptHandle>();
  const view = render(
    <>
      <PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={jest.fn()} ref={handle} {...props} />
      <Examples onUse={(example) => handle.current?.fill(example)} />
    </>,
  );
  return { onSubmit, handle, user: userEvent.setup({ delay: null }), ...view };
}

describe("the box to type in", () => {
  test("test_there_is_one_labelled_box_and_a_button_to_search", () => {
    show();

    expect(screen.getAllByRole("textbox")).toEqual([box()]);
    expect(box()).toHaveAccessibleName(PROMPT.label);
    expect(box()).toHaveAccessibleDescription(PROMPT.hint);
    expect(screen.getByRole("button", { name: PROMPT.submit })).toHaveAttribute("type", "submit");
  });

  test("test_what_is_typed_is_sent_as_it_was_typed", async () => {
    const { user, onSubmit } = show();

    await user.type(box(), "  leafy, near a park  ");
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith("  leafy, near a park  ");
    expect(box()).toHaveValue("  leafy, near a park  ");
  });

  test("test_the_count_of_characters_left_shows_once_fewer_than_100_remain", () => {
    show({ maxText: 600 });

    fireEvent.input(box(), { target: { value: "x".repeat(500) } });
    expect(screen.queryByText(/characters? left/)).toBeNull();

    fireEvent.input(box(), { target: { value: "x".repeat(501) } });
    expect(screen.getByText(PROMPT.left(99))).toBeInTheDocument();
    expect(box()).toHaveAccessibleDescription(`${PROMPT.hint} ${PROMPT.left(99)}`);

    fireEvent.input(box(), { target: { value: "x".repeat(599) } });
    expect(screen.getByText("1 character left")).toBeInTheDocument();
    fireEvent.input(box(), { target: { value: "x".repeat(600) } });
    expect(screen.getByText("0 characters left")).toBeInTheDocument();
  });

  test("test_the_box_takes_no_more_than_the_api_does", () => {
    show({ maxText: 321 });

    expect(box()).toHaveAttribute("maxlength", "321");
  });

  test("test_the_space_for_the_count_is_kept_so_nothing_moves_when_it_shows", () => {
    const { container } = show();
    const before = container.querySelectorAll("form > *").length;

    fireEvent.input(box(), { target: { value: "x".repeat(580) } });

    expect(container.querySelectorAll("form > *")).toHaveLength(before);
  });

  test("test_while_reading_the_button_says_so_and_there_is_a_way_to_stop", async () => {
    const { user, onSubmit, onStop } = show({ busy: true });

    expect(screen.getByRole("button", { name: PROMPT.reading })).toHaveAttribute("aria-disabled", "true");
    // It is not disabled outright, so the focus is not thrown off it.
    expect(screen.getByRole("button", { name: PROMPT.reading })).toBeEnabled();
    fireEvent.input(box(), { target: { value: "leafy" } });
    await user.click(screen.getByRole("button", { name: PROMPT.reading }));
    expect(onSubmit).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: PROMPT.stop }));
    expect(onStop).toHaveBeenCalledTimes(1);
  });

  test("test_the_apis_refusal_is_said_under_the_box_and_tied_to_it", () => {
    show({ refusal: "The text must be 1 to 600 characters." });

    expect(screen.getByRole("alert")).toHaveTextContent("The text must be 1 to 600 characters.");
    expect(box()).toHaveAccessibleDescription(
      `${PROMPT.hint} The text must be 1 to 600 characters.`,
    );
    expect(box()).toBeInvalid();
  });

  test("test_the_browser_is_not_asked_to_check_the_spelling_of_what_is_typed", () => {
    show();

    // A browser's fuller spell check sends what is in a checked field to its maker, which is
    // a second place for the words to go. Left unset, a textarea is checked.
    expect(box()).toHaveAttribute("spellcheck", "false");
    expect(box()).toHaveAttribute("autocomplete", "off");
    expect(box()).not.toHaveAttribute("name");
    expect(box().closest("form")).toHaveAttribute("method", "post");
  });

  test("test_the_line_under_the_box_says_how_words_are_handled_and_links_to_methods", () => {
    show({ reader: byRules });

    expect(screen.getByText(WORDS_LINE, { exact: false })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: PROMPT.wordsLink })).toHaveAttribute("href", "/methods#words");
  });

  test("test_who_else_reads_what_is_typed_is_said_in_the_services_own_words_before_anything_is_typed", () => {
    const { rerender, onSubmit, onStop } = show({ reader: byAModel });
    const said = () => screen.getByRole("group", { name: READER.label });

    // All of it, as it was served: whose model reads, what goes with it, and a link to
    // the company's own terms. The address is the service's, and the website writes none.
    expect(byAModel.model_reads).toBe(true);
    expect(said()).toHaveTextContent(byAModel.notice);
    expect(byAModel.terms_url).toMatch(/^https:\/\//);
    expect(within(said()).getByRole("link", { name: READER.terms })).toHaveAttribute("href", byAModel.terms_url);
    expect(box()).toHaveValue("");

    rerender(<PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} reader={withSettings} />);
    expect(withSettings.settings_sent).toBe(true);
    expect(said()).toHaveTextContent(withSettings.notice);
    expect(withSettings.notice).not.toBe(byAModel.notice);
  });

  test("test_where_no_model_reads_the_line_says_that_nothing_typed_is_sent_to_one", () => {
    show({ reader: byRules });

    expect(byRules.model_reads).toBe(false);
    expect(screen.getByRole("group", { name: READER.label })).toHaveTextContent(byRules.notice);
    expect(byRules.notice).toContain("not sent to a language model");
    // No company reads, so there are no terms of a company's to lead to.
    expect(screen.queryByRole("link", { name: READER.terms })).toBeNull();
  });

  test("test_until_the_service_has_said_who_reads_the_line_says_so_and_names_nobody", () => {
    const { rerender, onSubmit, onStop } = show();
    const said = () => screen.getByRole("group", { name: READER.label });

    expect(said()).toHaveTextContent(READER.checking);
    expect(said()).not.toHaveTextContent(byRules.notice);
    expect(said()).not.toHaveTextContent(byAModel.company ?? "no company");

    rerender(<PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} readerFailed />);
    expect(said()).toHaveTextContent(READER.unsaid);
    expect(said()).not.toHaveTextContent(READER.checking);
  });

  test("test_once_a_search_is_open_how_words_are_handled_is_one_press_away", () => {
    // The answer comes first. The line is said in full before anything is sent, and on Methods.
    show({ open: true });

    expect(screen.queryByText(WORDS_LINE, { exact: false })).toBeNull();
    expect(screen.getByRole("link", { name: PROMPT.wordsLink })).toHaveAttribute("href", "/methods#words");
  });

  test("test_once_a_search_is_open_the_box_is_one_line_high", () => {
    const { rerender } = render(<PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} />);
    expect(box()).toHaveAttribute("rows", "2");

    rerender(<PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} open />);

    expect(box()).toHaveAttribute("rows", "1");
    expect(screen.queryByText(PROMPT.hint)).toBeNull();
  });

  test("test_a_box_of_one_line_shows_one_line_whole_and_no_part_of_a_second", () => {
    // Seen in a browser: after a search the box was one line high and held a long sentence,
    // so the top of its second line showed under the first, cut through the middle.
    const rules = rulesOf(readFileSync(path.join(__dirname, "PromptBox.module.css"), "utf8"));
    const resting = rules.filter((rule) => /data-open="true"/.test(rule.selector) && /\.box\[data-tall="false"\]/.test(rule.selector));

    // While nobody types in it, what it holds is kept on one line, and what does not fit is out of sight.
    expect(resting.map((rule) => rule.sets.get("white-space"))).toEqual(["pre"]);
    expect(resting.map((rule) => rule.sets.get("overflow"))).toEqual(["hidden"]);
    // While it is typed in, it wraps as any box does, so that what is typed or selected is in sight.
    const typing = rules.filter((rule) => /data-open="true"/.test(rule.selector) && /\.box\[data-tall="true"\]/.test(rule.selector));
    expect(typing.map((rule) => rule.sets.get("min-height")).filter(Boolean)).toHaveLength(1);
  });

  test("test_the_box_is_as_high_as_it_was_until_a_press_elsewhere_has_landed", async () => {
    // Seen in a browser, five times of five: with the focus the box was three lines high.
    // A press on anything under it took the focus, the box dropped to one line, and what was
    // under it jumped up between the button going down and coming up. The press landed on
    // nothing. How high the box is now follows the press, and never the focus alone.
    const pressed = jest.fn();
    const { user } = show({ open: true, children: <button onClick={pressed}>Under the box</button> });
    const under = screen.getByRole("button", { name: "Under the box" });

    await user.click(box());
    expect(box()).toHaveFocus();
    expect(box()).toHaveAttribute("data-tall", "true");

    // The button goes down on what is under the box, and the focus leaves the box.
    await user.pointer({ keys: "[MouseLeft>]", target: under });
    expect(box()).not.toHaveFocus();
    expect(box()).toHaveAttribute("data-tall", "true");

    // It comes up, the press lands, and only then is the box one line again.
    await user.pointer({ keys: "[/MouseLeft]", target: under });
    expect(pressed).toHaveBeenCalledTimes(1);
    expect(box()).toHaveAttribute("data-tall", "false");
  });

  test("test_the_box_is_one_line_once_a_sentence_is_sent_though_the_focus_is_still_in_it", async () => {
    // After Enter the focus stays in the box. The answer comes first, so the box gives its
    // room back when the sentence is sent, and takes it again when the next word is typed.
    const { user, onSubmit } = show({ open: true });

    await user.type(box(), "leafy");
    expect(box()).toHaveAttribute("data-tall", "true");

    await user.keyboard("{Enter}");
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(box()).toHaveFocus();
    expect(box()).toHaveAttribute("data-tall", "false");

    await user.keyboard(" and quiet");
    expect(box()).toHaveAttribute("data-tall", "true");
  });

  test("test_leaving_the_box_by_keyboard_makes_it_one_line_at_once", async () => {
    const { user } = show({ open: true });

    await user.click(box());
    expect(box()).toHaveAttribute("data-tall", "true");
    // No press is under way, so nothing can be missed.
    await user.tab();

    expect(box()).not.toHaveFocus();
    expect(box()).toHaveAttribute("data-tall", "false");
  });

  test("test_words_that_are_selected_in_the_box_are_given_room_to_be_seen", () => {
    const { handle } = show({ open: true });
    fireEvent.input(box(), { target: { value: "leafy, and nothing like where I live now" } });
    fireEvent.blur(box());

    act(() => handle.current?.select({ start: 7, end: 40 }));

    expect(box()).toHaveFocus();
    expect(box()).toHaveAttribute("data-tall", "true");
    expect([box().selectionStart, box().selectionEnd]).toEqual([7, 40]);
  });

  test("test_there_are_three_examples_and_each_fills_the_box", async () => {
    const { user, onSubmit } = showWithExamples();

    for (const example of EXAMPLES) {
      await user.click(screen.getByRole("button", { name: example }));
      expect(box()).toHaveValue(example);
    }
    expect(EXAMPLES).toHaveLength(3);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  test("test_the_page_can_read_the_box_to_send_it_again_and_keeps_no_copy", async () => {
    const { user, handle } = show();

    await user.type(box(), "leafy");
    expect(handle.current?.text()).toBe("leafy");
    await user.type(box(), " and quiet");
    expect(handle.current?.text()).toBe("leafy and quiet");
  });

  test("test_once_a_search_is_open_the_box_says_that_what_is_typed_adds_to_it", () => {
    // Seen in a browser: a second example, and a second sentence, were added to the search
    // that was open, and nothing said so. The box read as it did on a first visit.
    const { rerender } = render(<PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} />);
    expect(box()).toHaveAccessibleName(PROMPT.label);

    rerender(
      <PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} onStartAgain={jest.fn()} open />,
    );

    // The label itself says so, where it is seen, and the way to begin a new one is beside the box.
    expect(box()).toHaveAccessibleName(PROMPT.labelOpen);
    expect(screen.getByText(PROMPT.labelOpen)).toBeVisible();
    expect(PROMPT.labelOpen).toMatch(/^Add to/);
    expect(screen.getByRole("button", { name: PROMPT.startAgain })).toBeVisible();
  });

  test("test_once_a_search_is_open_there_is_a_way_to_start_again_beside_the_box", async () => {
    // Seen in a browser: "Start again" was offered only after a failure.
    const onStartAgain = jest.fn();
    const { user } = show({ open: true, onStartAgain });
    await user.type(box(), "leafy");

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));

    expect(onStartAgain).toHaveBeenCalledTimes(1);
    // A new search starts from an empty box, with the focus in it.
    expect(box()).toHaveValue("");
    expect(box()).toHaveFocus();
  });

  test("test_before_a_search_there_is_nothing_to_start_again", () => {
    show({ onStartAgain: jest.fn() });

    expect(screen.queryByRole("button", { name: PROMPT.startAgain })).toBeNull();
  });

  test("test_what_burro_says_of_a_search_is_drawn_directly_under_the_box", () => {
    // Seen in a browser: after Search nothing on screen changed. What was understood stood
    // under the examples, the tenure and the place field, a screen and a half down a phone.
    const { container } = render(
      <PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} open>
        <p>what was understood</p>
      </PromptBox>,
    );
    const after = [...container.querySelectorAll("textarea ~ *, form ~ *")].map((element) => element.textContent);
    const between = [...container.querySelectorAll("form ~ *")].map((element) => element.textContent);

    // Nothing stands between the form that holds the box and what Burro says.
    expect(between).toEqual(["what was understood"]);
    expect(after.at(-1)).toBe("what was understood");
  });

  test("test_the_page_is_told_when_what_is_in_the_box_changes", async () => {
    const onTyped = jest.fn();
    const { user } = showWithExamples({ onTyped });

    await user.type(box(), "ab");
    expect(onTyped).toHaveBeenCalledTimes(2);

    await user.click(screen.getByRole("button", { name: EXAMPLES[0] as string }));
    expect(onTyped).toHaveBeenCalledTimes(3);
  });

  test("test_the_page_can_have_a_part_of_what_is_in_the_box_selected_and_the_words_never_leave_it", async () => {
    const { user, handle, container } = show();
    await user.type(box(), "Llamas please. A park nearby.");
    await user.tab();

    handle.current?.select({ start: 0, end: 14 });

    expect(box()).toHaveFocus();
    expect([box().selectionStart, box().selectionEnd]).toEqual([0, 14]);
    // Selected where it stands. It is written nowhere else on the page.
    const outside = container.cloneNode(true) as HTMLElement;
    outside.querySelectorAll("textarea").forEach((one) => one.remove());
    expect(outside.textContent?.includes("Llamas")).toBe(false);
    expect(outside.innerHTML.includes("Llamas")).toBe(false);
  });

  test("test_a_key_pressed_to_pick_a_character_does_not_send", () => {
    const { onSubmit } = show();
    fireEvent.input(box(), { target: { value: "に" } });

    fireEvent.keyDown(box(), { key: "Enter", isComposing: true });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  test("test_the_box_has_no_accessibility_fault", async () => {
    const { container } = show({ refusal: "The text must be 1 to 600 characters." });

    expect(await faultsIn(container)).toEqual([]);
  });
});
