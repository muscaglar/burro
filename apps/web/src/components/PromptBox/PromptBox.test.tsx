import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";

import { EXAMPLES, PROMPT } from "@/content/search";
import { WORDS_LINE } from "@/content/site";

import { faultsIn } from "../../../test/support/axe";
import { PromptBox, type PromptHandle } from "./PromptBox";

function show(props: Partial<Parameters<typeof PromptBox>[0]> = {}) {
  const onSubmit = jest.fn();
  const onStop = jest.fn();
  const handle = createRef<PromptHandle>();
  const view = render(
    <PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} ref={handle} {...props} />,
  );
  return { onSubmit, onStop, handle, user: userEvent.setup({ delay: null }), ...view };
}

const box = () => screen.getByRole<HTMLTextAreaElement>("textbox", { name: PROMPT.label });

describe("the box to type in", () => {
  test("test_there_is_one_labelled_box_and_a_button_to_search", () => {
    show();

    expect(screen.getAllByRole("textbox")).toEqual([box()]);
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
    show();

    expect(screen.getByText(WORDS_LINE, { exact: false })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: PROMPT.wordsLink })).toHaveAttribute("href", "/methods");
  });

  test("test_there_are_three_examples_and_each_fills_the_box", async () => {
    const { user, onSubmit } = show();

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
    expect(box()).toHaveAccessibleDescription(PROMPT.hint);

    rerender(<PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} open />);

    expect(box()).toHaveAccessibleDescription(PROMPT.hintOpen);
    expect(screen.getByText(PROMPT.hintOpen)).toBeVisible();
    expect(PROMPT.hintOpen).toMatch(/added to/);
    expect(PROMPT.hintOpen).toContain(PROMPT.startAgain);
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

  test("test_the_examples_are_for_a_first_search_and_go_once_one_is_open", () => {
    // An example fills the box with a whole search. Pressed over a search that is open, it
    // would be added to it: "Buying a terraced house" on top of "leafy and quiet".
    show({ open: true });

    expect(screen.queryByRole("heading", { name: PROMPT.examplesTitle })).toBeNull();
    for (const example of EXAMPLES) expect(screen.queryByRole("button", { name: example })).toBeNull();
  });

  test("test_what_burro_says_of_a_search_is_drawn_directly_under_the_box_and_before_the_examples", () => {
    // Seen in a browser: after Search nothing on screen changed. What was understood stood
    // under the examples, the tenure and the place field, a screen and a half down a phone.
    const { container } = render(
      <PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()}>
        <p>what was understood</p>
      </PromptBox>,
    );
    const inOrder = [...container.querySelectorAll("textarea, p, h2")].map((element) =>
      element.tagName === "TEXTAREA" ? "box" : (element.textContent ?? ""),
    );
    const at = (text: string) => inOrder.findIndex((one) => one.startsWith(text));

    expect(at("box")).toBeLessThan(at("what was understood"));
    expect(at(WORDS_LINE)).toBeLessThan(at("what was understood"));
    expect(at("what was understood")).toBeLessThan(at(PROMPT.examplesTitle));
  });

  test("test_the_page_is_told_when_what_is_in_the_box_changes", async () => {
    const onTyped = jest.fn();
    const { user } = show({ onTyped });

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
