import { readFileSync } from "node:fs";
import path from "node:path";

import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";

import { ADDED } from "@/content/added";
import { HELPERS } from "@/content/helpers";
import { EXAMPLES, PROMPT, SUGGEST } from "@/content/search";
import { WORDS_LINE } from "@/content/site";
import { REFINE, WAYS } from "@/content/ways";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Change } from "@/lib/search/mark";
import { NO_MARKS, type Marks } from "@/lib/search/store";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { Helpers } from "../Helpers/Helpers";
import { HELP_ON_A_NARROW_SCREEN, HELP_STANDS } from "./look";
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
// model does, and where the search settings are sent with the words. The box draws none.
const SAID_OF_WHO_READS = ["meta", "meta-model-reads", "meta-model-reads-with-settings"].map(
  (recorded) => recordedAnswer("get_meta", recorded).body.data.reader.notice,
);

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

  test("test_a_box_sent_with_nothing_in_it_sends_nothing_and_says_the_other_way_in_by_its_name", async () => {
    // It said "or use the settings". Before a search the settings stand in the second way
    // in, and once one is open in the part that refines it: each is named where it is said.
    const { user, onSubmit, rerender, onStop } = show();

    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(PROMPT.empty);
    expect(PROMPT.empty).toContain(WAYS.deep);
    expect(box()).toHaveFocus();
    expect(box()).toHaveAccessibleDescription(expect.stringContaining(PROMPT.empty));

    rerender(<PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} open />);
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(PROMPT.emptyOpen);
    expect(PROMPT.emptyOpen).toContain(REFINE.label);
    expect(PROMPT.emptyOpen).not.toContain(WAYS.deep);
  });

  test("test_what_is_pasted_and_fills_the_box_is_said_to_have_been_cut_where_it_may_have_been", () => {
    // Seen in a browser: 900 characters were pasted, the box held 600 of them and ended in
    // the middle of a word, and the count said "0 characters left". Nothing said that the
    // end had been left out, and the search read a sentence that was cut short.
    show({ maxText: 600 });
    const pasted = (value: string, inputType = "insertFromPaste") =>
      fireEvent.input(box(), { target: { value }, inputType });
    const said = () => screen.queryAllByRole("status").map((line) => line.textContent);

    // A browser cuts what is pasted at what the box takes, and the box is then full.
    pasted("x".repeat(600));
    expect(said()).toEqual([PROMPT.full(600)]);
    expect(PROMPT.full(600)).toMatch(/\b600 characters\b/);
    expect(box()).toHaveAccessibleDescription(expect.stringContaining(PROMPT.full(600)));
    // It is no fault of the person's, and is not said as one.
    expect(screen.queryByRole("alert")).toBeNull();
    expect(box()).not.toHaveAttribute("aria-invalid");
    // It goes as the box is next changed.
    fireEvent.input(box(), { target: { value: "x".repeat(599) }, inputType: "deleteContentBackward" });
    expect(said()).toEqual([]);

    // What is dropped into the box is cut as what is pasted is.
    pasted("x".repeat(600), "insertFromDrop");
    expect(said()).toEqual([PROMPT.full(600)]);
    // What is pasted and leaves room was taken whole, and what is typed to the last
    // character was typed by a person who saw the count.
    pasted("x".repeat(599));
    expect(said()).toEqual([]);
    fireEvent.input(box(), { target: { value: "x".repeat(600) }, inputType: "insertText" });
    expect(said()).toEqual([]);
  });

  test("test_once_a_search_is_open_the_box_is_full_where_what_would_be_sent_is_as_much_as_burro_reads", () => {
    // What the search has read stays in the box, and takes none of the room for what is added.
    const first = "leafy and quiet";
    const { marks } = readTo(first.length);
    render(<PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} open marks={marks} />);

    fireEvent.input(box(), { target: { value: first }, inputType: "insertText" });
    fireEvent.input(box(), { target: { value: `${first}${"x".repeat(599)}` }, inputType: "insertFromPaste" });
    expect(screen.queryByText(PROMPT.full(600))).toBeNull();
    fireEvent.input(box(), { target: { value: `${first}${"x".repeat(600)}` }, inputType: "insertFromPaste" });
    expect(screen.getByText(PROMPT.full(600))).toBeInTheDocument();
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

  test.each([
    ["before a search", false],
    ["once a search is open", true],
  ])("test_nothing_in_the_box_says_how_words_are_handled_or_who_reads_them: %s", (_, open) => {
    // The founder walked the page and had the lines under the box go, with the link beside
    // them, before a search and after one. The foot of every page leads to how words are
    // handled, and the page of methods says all of it.
    const { container } = show({ open });
    const said = container.textContent ?? "";

    expect(screen.queryByRole("group")).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
    expect(said.includes(WORDS_LINE)).toBe(false);
    expect(said).not.toMatch(/What you type is/);
    expect(said).not.toMatch(/language model/i);
    // Nor what stood in their place until the service had said who reads, or could not.
    expect(said).not.toMatch(/who else reads/i);
    for (const notice of SAID_OF_WHO_READS) expect(said.includes(notice)).toBe(false);
  });

  test("test_the_box_asks_what_is_important_and_says_what_a_useful_sentence_holds", () => {
    const [example] = EXAMPLES;
    show({ example });

    expect(PROMPT.label).toBe("Tell me what's important in your space");
    expect(box()).toHaveAccessibleName(PROMPT.label);
    // What helps most: what can be spent, where to get to and how long that may take, and
    // what is wanted nearby. And that more words make a closer match.
    const help = screen.getByText(PROMPT.hint);
    expect(PROMPT.hint).toMatch(/what you can spend/);
    expect(PROMPT.hint).toMatch(/where you need to get to and how long that journey may take/);
    expect(PROMPT.hint).toMatch(/what you want around you/);
    expect(PROMPT.hint).toMatch(/The more you say, the closer/);
    // One whole sentence as an example, which is the one it was handed and no other.
    const quoted = screen.getByText(example as string);
    expect(quoted.tagName).toBe("Q");
    expect(quoted.parentElement).toHaveTextContent(`${PROMPT.forExample} ${example}`);
    expect(help.compareDocumentPosition(quoted) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // All of it is said of the box, to whoever hears the page, and stands over the field.
    expect(box()).toHaveAccessibleDescription(`${PROMPT.hint} ${PROMPT.forExample} ${example}`);
    expect(quoted.compareDocumentPosition(box()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  test("test_where_the_data_gives_no_example_the_box_offers_none_and_no_words_that_lead_to_one", () => {
    const { container } = show({ example: null });

    expect(container.querySelector("q")).toBeNull();
    expect(container.textContent?.includes(PROMPT.forExample)).toBe(false);
    expect(box()).toHaveAccessibleDescription(PROMPT.hint);
  });

  test("test_on_a_narrow_screen_what_a_useful_sentence_holds_stands_under_the_field_and_the_field_is_the_field_it_was", () => {
    // Measured on a phone, 390 by 844, with the sentences over the field: the field stood
    // from 896 to 967, under the foot of the first screen. Under the field they leave it
    // where it was, from 708. On a wider screen they stand over it, where there is room.
    const [example] = EXAMPLES;
    const { rerender, onSubmit, onStop } = show({ example });
    const help = () => screen.getByText(PROMPT.hint);
    const field = box();
    fireEvent.input(field, { target: { value: "leafy" } });

    expect(help().compareDocumentPosition(box()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    rerender(<PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} example={example} narrow />);

    // The order of the page is the order it is drawn in: the sentences come after the field.
    expect(box().compareDocumentPosition(help()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByText(example as string).compareDocumentPosition(box()) & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy();
    // What was typed is in the box still: the field was not drawn anew.
    expect(box()).toBe(field);
    expect(box()).toHaveValue("leafy");
    expect(box()).toHaveAccessibleDescription(`${PROMPT.hint} ${PROMPT.forExample} ${example}`);
  });

  test("test_on_a_narrow_screen_what_burro_says_stands_directly_under_the_field_and_the_sentences_come_after_it", () => {
    // Seen on a phone, with the service out of reach: a person pressed Search, and what
    // said that Burro could not be reached stood under the sentences that say what a useful
    // sentence holds, 153 px under the foot of the window. The page looked as it had.
    const [example] = EXAMPLES;
    const said = (
      <p role="alert">Burro could not be reached.</p>
    );
    const { rerender } = render(
      <PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} example={example} narrow>
        {said}
      </PromptBox>,
    );
    const follows = (one: Element, other: Element) =>
      Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);
    const help = () => screen.getByText(PROMPT.hint);
    const alert = () => screen.getByRole("alert");

    // The field and Search, then what Burro says, then the sentences that help.
    expect(follows(box(), alert())).toBe(true);
    expect(follows(screen.getByRole("button", { name: PROMPT.submit }), alert())).toBe(true);
    expect(follows(alert(), help())).toBe(true);
    // Nothing that is pressed stands between the field and what Burro says but the buttons of the box.
    const between = [...document.querySelectorAll("button, a, input, select")].filter(
      (one) => follows(box(), one) && follows(one, alert()),
    );
    expect(between.map((one) => one.textContent)).toEqual([PROMPT.submit]);
    // All that the sentences say is said of the field still, wherever they stand.
    expect(box()).toHaveAccessibleDescription(`${PROMPT.hint} ${PROMPT.forExample} ${example}`);

    // On a wider screen they stand over the field, and what Burro says under it, as it did.
    rerender(
      <PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} example={example}>
        {said}
      </PromptBox>,
    );
    expect(follows(help(), box())).toBe(true);
    expect(follows(box(), alert())).toBe(true);
  });

  test("test_the_sentences_are_drawn_under_the_field_on_a_narrow_screen_before_the_page_has_asked_which_screen_there_is", () => {
    // The page is built with no screen to ask, with the sentences over the field, and the
    // sheet draws them under it on a narrow screen: so nothing moves when the page has asked.
    const { container } = show();
    const narrow = RULES.filter((rule) => rule.under === "@media (max-width: 40rem)" && rule.sets.has("order"));

    expect(container.firstElementChild).toHaveAttribute("data-help", HELP_ON_A_NARROW_SCREEN);
    expect(narrow.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      ['.prompt[data-help="under"] .hint', [["order", "1"]]],
    ]);
    // Nothing else of the box is drawn out of the order it stands in.
    expect(RULES.filter((rule) => rule.sets.has("order")).length).toBe(1);
  });

  test("test_one_line_of_the_look_has_the_sentences_stand_over_the_field_on_a_narrow_screen_too", () => {
    const { container } = show({ narrow: true, help: "over" });

    expect(HELP_STANDS).toEqual(["under", "over"]);
    expect(HELP_ON_A_NARROW_SCREEN).toBe("under");
    expect(container.firstElementChild).toHaveAttribute("data-help", "over");
    expect(screen.getByText(PROMPT.hint).compareDocumentPosition(box()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  test("test_the_example_is_shown_and_nothing_of_it_is_put_in_the_box_or_sent", async () => {
    const [example] = EXAMPLES;
    const { user, onSubmit } = show({ example });

    await user.click(screen.getByText(example as string));

    expect(box()).toHaveValue("");
    expect(onSubmit).not.toHaveBeenCalled();
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

    act(() => handle.current?.select({ start: 0, end: 14 }));

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

// A string found nowhere else, planted in what a person types.
const CANARY = "zqxcanary7431";

/** What a box is told by a search that has read so much of it, and what the box tells it. */
function readTo(to: number, more: Partial<Marks> = {}) {
  const edited = jest.fn<void, [Change]>();
  const found = jest.fn<void, [number]>();
  const marks: Marks = { ...NO_MARKS, read: { to, changed: false }, from: to, edited, found, ...more };
  return { marks, edited, found };
}

describe("a box that holds words the search has read", () => {
  const first = "leafy and quiet";
  const more = ", near a park";
  /** The same with a word of it changed, which leaves it as long as it was. */
  const changed = "leafy but quiet";

  test("test_what_is_sent_is_what_stands_after_the_words_that_were_read", async () => {
    const { marks } = readTo(first.length);
    const { user, onSubmit } = show({ open: true, marks });
    fireEvent.input(box(), { target: { value: `${first}${more}` } });

    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    // As it was typed, with the comma it begins with. The words before it are not sent again.
    expect(onSubmit.mock.calls).toEqual([[more]]);
    // The box keeps all of it.
    expect(box().value === `${first}${more}`).toBe(true);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.queryByRole("status")).toBeNull();
  });

  test("test_search_with_nothing_new_in_the_box_sends_nothing_and_says_why", async () => {
    // It sent all that the box held a second time, and the words were read onto the search again.
    const { marks } = readTo(first.length);
    const { user, onSubmit } = show({ open: true, marks });
    fireEvent.input(box(), { target: { value: first } });

    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(ADDED.nothingNew);
    expect(box()).toHaveAccessibleDescription(ADDED.nothingNew);
    // The focus is in the box, where what is to be added is typed.
    expect(box()).toHaveFocus();
    // Space after what was read is nothing new either.
    fireEvent.input(box(), { target: { value: `${first}  ` } });
    expect(screen.queryByRole("alert")).toBeNull();
    await user.keyboard("{Enter}");
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(ADDED.nothingNew);
  });

  test("test_while_a_model_reads_the_words_the_box_says_that_they_are_being_read", async () => {
    // Search pressed a second time, with the box as it was, while a model read. The words
    // are not sent again, and are not said to have been read while they are being read.
    const { marks } = readTo(first.length, { reading: true });
    const { user, onSubmit, onStop, rerender } = show({ open: true, marks });
    fireEvent.input(box(), { target: { value: first } });

    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent(SUGGEST.reading);
    // It goes when the model has read them.
    rerender(
      <PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} open marks={readTo(first.length).marks} />,
    );
    expect(screen.queryByRole("status")).toBeNull();
  });

  test("test_a_change_to_words_that_were_read_is_not_sent_and_the_box_says_so", async () => {
    const { marks } = readTo(first.length, { read: { to: first.length, changed: true } });
    const { user, onSubmit } = show({ open: true, marks });
    fireEvent.input(box(), { target: { value: changed } });

    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(ADDED.changed);
    expect(box()).toHaveFocus();
  });

  test("test_what_is_added_after_words_that_were_changed_is_sent_and_the_change_is_said_not_to_be_read", async () => {
    const { marks } = readTo(first.length, { read: { to: first.length, changed: true } });
    const { user, onSubmit, onStop, rerender } = show({ open: true, marks });
    fireEvent.input(box(), { target: { value: `${changed}${more}` } });

    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    expect(onSubmit.mock.calls).toEqual([[more]]);
    // Nothing is said of words that are not yet read: they may not reach Burro at all.
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.queryByRole("status")).toBeNull();

    // They are read. It is said as what happened, and not as a fault: what was added was read.
    const all = `${changed}${more}`.length;
    rerender(
      <PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} open marks={readTo(all).marks} />,
    );
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent(ADDED.changedToo);
    expect(box()).toHaveAccessibleDescription(ADDED.changedToo);
  });

  test("test_what_the_box_said_goes_when_the_box_is_changed", async () => {
    const { marks } = readTo(first.length);
    const { user } = show({ open: true, marks });
    fireEvent.input(box(), { target: { value: first } });
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));
    expect(screen.getByRole("alert")).toBeInTheDocument();

    await user.type(box(), " and");

    expect(screen.queryByRole("alert")).toBeNull();
    expect(box()).not.toBeInvalid();
  });

  test("test_that_what_was_added_was_read_by_itself_is_said_under_the_box", () => {
    const { marks } = readTo(first.length, { apart: true });
    show({ open: true, marks });

    expect(screen.getByRole("status")).toHaveTextContent(ADDED.apart);
    expect(box()).toHaveAccessibleDescription(ADDED.apart);
    // It stands in the form that holds the box, so that nothing stands between the form and what Burro says.
    expect(screen.getByRole("status").closest("form")).toBe(box().closest("form"));
  });

  test("test_the_page_is_handed_the_words_that_were_sent_and_selects_among_them", () => {
    // The service counts where words stand from the start of what it was sent.
    const { marks } = readTo(first.length + more.length, { from: first.length });
    const { handle } = show({ open: true, marks });
    fireEvent.input(box(), { target: { value: `${first}${more}` } });

    expect(handle.current?.text()).toBe(more);
    act(() => handle.current?.select({ start: 2, end: 6 }));

    expect(box()).toHaveFocus();
    expect(box().value.slice(box().selectionStart, box().selectionEnd)).toBe("near");
    expect(more.slice(2, 6)).toBe("near");
  });

  test("test_what_is_selected_is_brought_into_sight_by_the_caret_at_its_end", () => {
    // Seen in a browser: words were selected under the three lines that the box shows, and
    // the box went on showing its first three. A browser brings the caret into sight when
    // a box takes the focus, and what is selected not at all.
    const { handle } = show({ open: true });
    fireEvent.input(box(), { target: { value: `${first}${more}` } });
    act(() => box().focus());
    const done: string[] = [];
    const selected = jest.spyOn(box(), "setSelectionRange");
    selected.mockImplementation((start, end) => void done.push(`caret ${start} to ${end}`));
    box().addEventListener("blur", () => done.push("left"));
    box().addEventListener("focus", () => done.push("taken"));

    act(() => handle.current?.select({ start: 17, end: 21 }));

    expect(done).toEqual(["left", "caret 21 to 21", "taken", "caret 17 to 21"]);
    expect(box()).toHaveAttribute("data-tall", "true");
    selected.mockRestore();
  });

  test("test_what_the_search_has_read_takes_none_of_the_room_for_what_is_added", () => {
    const { marks } = readTo(first.length);
    show({ open: true, maxText: 600, marks });

    expect(box()).toHaveAttribute("maxlength", String(first.length + 600));
    fireEvent.input(box(), { target: { value: `${first}${"x".repeat(500)}` } });
    expect(screen.queryByText(/characters? left/)).toBeNull();
    fireEvent.input(box(), { target: { value: `${first}${"x".repeat(501)}` } });
    expect(screen.getByText(PROMPT.left(99))).toBeInTheDocument();
  });

  test("test_the_box_says_how_much_it_holds_as_it_is_drawn", () => {
    const { marks, found } = readTo(first.length);

    show({ open: true, marks });

    // A box that is drawn is empty, whatever the search had read of the one before it.
    expect(found.mock.calls).toEqual([[0]]);
  });

  test("test_the_box_says_where_it_was_changed_in_counts_and_never_what_was_typed", async () => {
    const { marks, edited, found } = readTo(0);
    const { user } = show({ marks });

    await user.type(box(), `a ${CANARY}`);
    const typed = 2 + CANARY.length;
    expect(edited).toHaveBeenCalledTimes(typed);
    expect(edited.mock.calls[0]).toEqual([{ at: 0, out: 0, into: 1, holds: 1 }]);
    expect(edited.mock.lastCall).toEqual([{ at: typed - 1, out: 0, into: 1, holds: typed }]);

    // A letter typed among the others, a letter taken out, and a word typed over.
    await user.type(box(), "b", { initialSelectionStart: 1, initialSelectionEnd: 1 });
    expect(edited.mock.lastCall).toEqual([{ at: 1, out: 0, into: 1, holds: typed + 1 }]);
    await user.type(box(), "{Backspace}", { initialSelectionStart: 2, initialSelectionEnd: 2 });
    expect(edited.mock.lastCall).toEqual([{ at: 1, out: 1, into: 0, holds: typed }]);
    await user.type(box(), "c", { initialSelectionStart: 2, initialSelectionEnd: typed });
    expect(edited.mock.lastCall).toEqual([{ at: 2, out: CANARY.length, into: 1, holds: 3 }]);
    await user.clear(box());
    expect(edited.mock.lastCall).toEqual([{ at: 0, out: 3, into: 0, holds: 0 }]);

    // Every one of them is counts, and none holds a letter of what was typed.
    const told = [...edited.mock.calls, ...found.mock.calls].flat();
    expect(told.flatMap((one) => (typeof one === "number" ? [one] : Object.values(one))).every(Number.isInteger)).toBe(true);
    expect(JSON.stringify(told).includes(CANARY)).toBe(false);
  });

  test("test_a_box_that_was_changed_and_did_not_say_so_sends_nothing_that_may_have_been_read", async () => {
    // A tool that fills a box in may change it and tell nobody. Where it was changed,
    // nobody knows: so that no word is read a second time, none of it is sent.
    const { marks, edited } = readTo(first.length);
    const { user, onSubmit } = show({ open: true, marks });
    fireEvent.input(box(), { target: { value: first } });
    edited.mockClear();

    box().value = `${first}${more} ${CANARY}`;
    await user.click(screen.getByRole("button", { name: PROMPT.submit }));

    const all = first.length + more.length + 1 + CANARY.length;
    expect(edited.mock.calls).toEqual([[{ at: null, out: first.length, into: all, holds: all }]]);
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(ADDED.changed);
    // Where nothing of the box was read, all of it is new, and is sent.
    const fresh = show({ marks: readTo(0).marks });
    const other = screen.getAllByRole<HTMLTextAreaElement>("textbox").at(-1) as HTMLTextAreaElement;
    other.value = first;
    await fresh.user.click(screen.getAllByRole("button", { name: PROMPT.submit }).at(-1) as HTMLElement);
    expect(fresh.onSubmit.mock.calls).toEqual([[first]]);
  });

  /**
   * What a browser does when the keys that undo are pressed: the box holds what it held at
   * another time, with what came back selected or the caret after it, and says how it came to.
   */
  function putBack(holds: string, selected: { start: number; end: number }, inputType = "historyUndo") {
    box().value = holds;
    box().setSelectionRange(selected.start, selected.end);
    fireEvent.input(box(), { inputType });
  }

  /** Selects so much of the box, as a person does with the keys or by dragging over it. */
  async function select(user: ReturnType<typeof userEvent.setup>, start: number, end: number) {
    await user.click(box());
    box().setSelectionRange(start, end);
    fireEvent.select(box());
  }

  test("test_the_box_says_that_what_came_into_it_was_put_back_by_the_keys_that_undo", async () => {
    // Seen in a browser: what those keys put back stood after the place the search had read
    // to, and was sent as if it had been typed.
    const { marks, edited } = readTo(first.length);
    const { user } = show({ open: true, marks });
    fireEvent.input(box(), { target: { value: first } });

    // " quiet" is taken out, and the keys that undo put it back, selected as it was.
    await user.type(box(), "{Backspace}", { initialSelectionStart: 9, initialSelectionEnd: 15 });
    expect(edited.mock.lastCall).toEqual([{ at: 9, out: 6, into: 0, holds: 9 }]);
    putBack(first, { start: 9, end: 15 });
    expect(edited.mock.lastCall).toEqual([{ at: 9, out: 0, into: 6, holds: 15, how: "undone" }]);

    // The keys that do again take it out again, and say that it was they. The key that
    // puts back what a key took out undoes that.
    putBack("leafy and", { start: 9, end: 9 }, "historyRedo");
    expect(edited.mock.lastCall).toEqual([{ at: 9, out: 6, into: 0, holds: 9, how: "redone" }]);
    putBack(first, { start: 15, end: 15 }, "insertFromYank");
    expect(edited.mock.lastCall).toEqual([{ at: 9, out: 0, into: 6, holds: 15, how: "undone" }]);

    // What is typed says nothing of how it came.
    await user.type(box(), "!");
    expect(edited.mock.lastCall).toEqual([{ at: 15, out: 0, into: 1, holds: 16 }]);
    expect(Object.keys(edited.mock.lastCall?.[0] ?? {})).toEqual(["at", "out", "into", "holds"]);
  });

  test("test_what_the_box_says_of_how_words_came_is_a_name_of_few_and_never_a_word_of_them", async () => {
    const { marks, edited } = readTo(CANARY.length + 6);
    const { user } = show({ open: true, marks });
    const sentence = `leafy ${CANARY}`;
    await user.type(box(), sentence);

    await user.type(box(), "{Backspace}", { initialSelectionStart: 6, initialSelectionEnd: sentence.length });
    putBack(sentence, { start: 6, end: sentence.length });
    await select(user, 0, sentence.length);
    await user.copy();
    await user.paste();

    putBack("leafy ", { start: 6, end: 6 }, "historyRedo");

    const told = edited.mock.calls.flat();
    expect(told.map((one) => one.how).filter((how) => how !== undefined)).toEqual(["undone", "pasted", "redone"]);
    const counts = told.flatMap((one) => Object.entries(one).filter(([name]) => name !== "how"));
    expect(counts.length).toBe(4 * told.length);
    expect(counts.every(([, count]) => Number.isInteger(count))).toBe(true);
    expect(JSON.stringify(told).includes(CANARY)).toBe(false);
  });

  test("test_the_box_says_that_what_is_pasted_had_been_in_it_where_it_was_taken_from_what_was_read", async () => {
    // A copy of the sentence pasted over it leaves the box as it was, and all of it was
    // sent again as if it had been typed.
    const { marks, edited } = readTo(first.length);
    const { user } = show({ open: true, marks });
    fireEvent.input(box(), { target: { value: first } });

    // " quiet" is cut out, and pasted where it stood.
    await select(user, 9, 15);
    await user.cut();
    expect(edited.mock.lastCall).toEqual([{ at: 9, out: 6, into: 0, holds: 9 }]);
    await user.paste();
    expect(box().value === first).toBe(true);
    expect(edited.mock.lastCall).toEqual([{ at: 9, out: 0, into: 6, holds: 15, how: "pasted" }]);

    // All of it is copied, and pasted over itself and then after itself.
    await select(user, 0, 15);
    await user.copy();
    await user.paste();
    expect(edited.mock.lastCall).toEqual([{ at: 0, out: 15, into: 15, holds: 15, how: "pasted" }]);
    await user.paste();
    expect(box().value === `${first}${first}`).toBe(true);
    expect(edited.mock.lastCall).toEqual([{ at: 15, out: 0, into: 15, holds: 30, how: "pasted" }]);
  });

  test("test_what_is_pasted_that_was_not_taken_from_what_was_read_is_new", async () => {
    const { marks, edited } = readTo(first.length);
    const { user, onSubmit, onStop, rerender } = show({ open: true, marks });
    fireEvent.input(box(), { target: { value: first } });

    // Words that were copied somewhere else, as a sentence written beforehand is.
    await user.click(box());
    await user.paste(more);
    expect(edited.mock.lastCall).toEqual([{ at: 15, out: 0, into: more.length, holds: 15 + more.length }]);
    // Words that stand after what was read, copied and pasted after themselves.
    await select(user, 15, 15 + more.length);
    await user.copy();
    box().setSelectionRange(box().value.length, box().value.length);
    await user.paste();
    expect(edited.mock.lastCall).toEqual([{ at: 15 + more.length, out: 0, into: more.length, holds: 15 + 2 * more.length }]);

    // What was read is copied, and then something else on the page is: as long, by chance.
    await select(user, 0, 15);
    await user.copy();
    fireEvent.copy(document.body);
    await user.paste("x".repeat(15));
    expect("how" in (edited.mock.lastCall?.[0] ?? {})).toBe(false);

    // What was read is copied, and the search begins again: it has read nothing of it.
    await select(user, 0, 15);
    await user.copy();
    const fresh = readTo(0);
    rerender(<PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} marks={fresh.marks} />);
    await user.paste();
    expect(fresh.edited.mock.lastCall?.[0]).toMatchObject({ into: 15 });
    expect("how" in (fresh.edited.mock.lastCall?.[0] ?? {})).toBe(false);
  });

  test("test_words_copied_before_they_were_read_are_not_new_once_they_are", async () => {
    // A person copies the sentence they typed, to keep it, and sends it. Pasted after
    // itself then, it is what the search has read.
    const before = readTo(0);
    const { user, onSubmit, onStop, rerender } = show({ marks: before.marks });
    await user.type(box(), first);
    await select(user, 0, 15);
    await user.copy();

    const { marks, edited } = readTo(first.length);
    rerender(<PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} marks={marks} open />);
    box().setSelectionRange(15, 15);
    await user.paste();

    expect(edited.mock.lastCall).toEqual([{ at: 15, out: 0, into: 15, holds: 30, how: "pasted" }]);
  });

  test("test_what_the_keys_that_undo_leave_selected_says_where_what_they_put_back_stands", async () => {
    // "quiet" was typed over "lively" before the sentence was sent. The keys that undo put
    // "lively" back where "quiet" stands, and leave it selected: six came and five went,
    // where the counts alone would say that one letter came at the end.
    const { marks, edited } = readTo(first.length);
    show({ open: true, marks });
    fireEvent.input(box(), { target: { value: first } });

    putBack("leafy and lively", { start: 10, end: 16 });

    expect(edited.mock.lastCall).toEqual([{ at: 10, out: 5, into: 6, holds: 16, how: "undone" }]);
    // With no more than a caret left after it, it is placed by where it ends.
    putBack(first, { start: 15, end: 15 }, "historyRedo");
    expect(edited.mock.lastCall).toEqual([{ at: 15, out: 1, into: 0, holds: 15, how: "redone" }]);
  });

  test("test_what_was_copied_is_known_for_read_once_it_is_sent_whatever_is_done_to_the_box_since", async () => {
    // Found by changing many boxes at random. A person copies the sentence they typed, and
    // sends it. They type over all of the box, so that nothing in it was read, and paste
    // the sentence after that: it was read, and is not new.
    const before = readTo(0);
    const { user, onSubmit, onStop, rerender } = show({ marks: before.marks });
    await user.type(box(), first);
    await select(user, 0, 15);
    await user.copy();
    await user.keyboard("{Enter}");
    expect(onSubmit.mock.calls).toEqual([[first]]);

    // The box is typed over while the sentence is read, so the place never reaches it.
    const { marks, edited } = readTo(0);
    rerender(<PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} marks={marks} open />);
    await user.type(box(), "x", { initialSelectionStart: 0, initialSelectionEnd: 15 });
    await user.paste();

    expect(box().value === `x${first}`).toBe(true);
    expect(edited.mock.lastCall).toEqual([{ at: 1, out: 0, into: 15, holds: 16, how: "pasted" }]);
  });

  test("test_what_was_copied_is_known_for_read_once_the_search_has_read_past_where_it_stood", async () => {
    // The sentence is copied before it is read, and read. All of the box is then typed
    // over, and the sentence pasted.
    const before = readTo(0);
    const { user, onSubmit, onStop, rerender } = show({ marks: before.marks });
    fireEvent.input(box(), { target: { value: first } });
    await select(user, 0, 15);
    await user.copy();
    rerender(<PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} marks={readTo(first.length).marks} open />);

    const { marks, edited } = readTo(0);
    rerender(<PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} marks={marks} open />);
    await user.type(box(), "x", { initialSelectionStart: 0, initialSelectionEnd: 15 });
    await user.paste();

    expect(edited.mock.lastCall).toEqual([{ at: 1, out: 0, into: 15, holds: 16, how: "pasted" }]);
  });

  test("test_an_example_and_starting_again_say_that_all_the_box_held_went", async () => {
    const { marks, edited } = readTo(0);
    const handle = createRef<PromptHandle>();
    const user = userEvent.setup({ delay: null });
    render(
      <PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} onStartAgain={jest.fn()} ref={handle} marks={marks} open />,
    );
    await user.type(box(), "leafy");
    const example = EXAMPLES[0] as string;

    act(() => handle.current?.fill(example));
    expect(edited.mock.lastCall).toEqual([{ at: 0, out: 5, into: example.length, holds: example.length }]);

    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));
    expect(edited.mock.lastCall).toEqual([{ at: 0, out: example.length, into: 0, holds: 0 }]);
    expect(box()).toHaveValue("");
  });

  test("test_the_box_with_what_it_says_of_what_was_added_has_no_accessibility_fault", async () => {
    const { marks } = readTo(first.length, { apart: true });
    const { container } = show({ open: true, marks });

    expect(await faultsIn(container)).toEqual([]);
  });
});

const CSS = readFileSync(path.join(__dirname, "PromptBox.module.css"), "utf8");
const RULES = rulesOf(CSS);
const setsOf = (selector: string) =>
  new Map(RULES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));
/** The box of the look that the field stands in. */
const frame = () => box().closest("[data-kind]") as HTMLElement;
/** What a button of the look is drawn as: cobalt, cream, cream with an edge of poppy, or amber. */
const drawnAs = (name: string) => screen.getByRole("button", { name }).querySelector("[data-kind]")?.getAttribute("data-kind");

describe("the box, as the look draws it", () => {
  test("test_the_box_is_a_box_of_the_look_and_is_the_box_in_hand_while_it_is_typed_in", async () => {
    const { user } = show();
    expect(frame()).toHaveAttribute("data-kind", "box");

    await user.click(box());
    expect(frame()).toHaveAttribute("data-kind", "box-on");

    // Left by keyboard, it is at rest at once.
    await user.tab();
    expect(frame()).toHaveAttribute("data-kind", "box");
  });

  test("test_the_box_is_in_hand_by_what_was_done_and_never_by_the_focus_alone", async () => {
    // It is one with how high the box is: a press elsewhere lands before anything changes,
    // and a sentence that is sent leaves the box at rest though the focus is still in it.
    const pressed = jest.fn();
    const { user, onSubmit } = show({ open: true, children: <button onClick={pressed}>Under the box</button> });
    await user.type(box(), "leafy");
    expect(frame()).toHaveAttribute("data-kind", "box-on");

    await user.pointer({ keys: "[MouseLeft>]", target: screen.getByRole("button", { name: "Under the box" }) });
    expect(box()).not.toHaveFocus();
    expect(frame()).toHaveAttribute("data-kind", "box-on");
    await user.pointer({ keys: "[/MouseLeft]", target: screen.getByRole("button", { name: "Under the box" }) });
    expect(pressed).toHaveBeenCalledTimes(1);
    expect(frame()).toHaveAttribute("data-kind", "box");

    await user.type(box(), "{Enter}");
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(box()).toHaveFocus();
    expect(frame()).toHaveAttribute("data-kind", "box");
    // No rule of the style sheet is keyed on the focus of the field or of the box.
    const keyed = RULES.filter((rule) => /:(focus|focus-within|focus-visible|hover|active)\b/.test(rule.selector));
    expect(keyed.map((rule) => rule.selector).filter((selector) => !/^\.example\b/.test(selector))).toEqual([]);
  });

  test("test_the_edge_of_the_field_is_whole_at_rest_and_in_hand_and_nothing_of_the_box_is_dashed", () => {
    // The founder, of the field as it was drawn at rest: "The dashed border is not understood
    // to a user, please make solid". It is a whole edge of ink, as wide as a rule of the
    // look, and it is the same edge in hand: what says the box is in hand is its frame.
    expect(setsOf(".box").get("border")).toBe("var(--edge) solid var(--border)");
    expect([...setsOf('.box[data-tall="true"]')]).toEqual([]);
    // Nor is any rule of it.
    const broken = RULES.flatMap((rule) => [...rule.sets].filter(([, value]) => /\b(dashed|dotted)\b/.test(value)));
    expect(broken).toEqual([]);
    expect(readFileSync(path.join(__dirname, "PromptBox.module.css"), "utf8")).not.toMatch(/dashed|dotted/);
  });

  test("test_what_burro_says_of_the_search_stands_in_the_box_under_the_field", () => {
    render(
      <PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} open>
        <p>what was understood</p>
      </PromptBox>,
    );

    expect(frame()).toContainElement(screen.getByText("what was understood"));
    expect(frame()).toContainElement(box().closest("form"));
  });

  test("test_in_a_window_that_is_wide_and_not_high_the_box_keeps_what_it_holds_closer_before_a_search", () => {
    // Measured at 1280 by 720, before a search: the three helpers under the box stood at the
    // very foot of the first screen, and 37 px under it. The field is as high as it was.
    const short = RULES.filter((rule) => rule.under === "@media (min-width: 60rem) and (max-height: 47.99rem)");

    expect(short.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      ['.prompt[data-open="false"]', [["padding-block", "var(--space-2)"]]],
    ]);
    expect(setsOf(".box").get("min-height")).toBe("calc(2 * var(--leading-text) * 1em + 2 * var(--space-2))");
  });

  test("test_search_is_cobalt_and_no_other_button_of_the_box_is", () => {
    const { rerender, onSubmit, onStop } = show({ open: true, onStartAgain: jest.fn() });

    expect(drawnAs(PROMPT.submit)).toBe("go");
    expect(drawnAs(PROMPT.startAgain)).toBe("plain");

    rerender(<PromptBox maxText={600} busy onSubmit={onSubmit} onStop={onStop} open onStartAgain={jest.fn()} />);
    // While a sentence is read the button keeps its colour and says that it is off. What
    // ends the reading has an edge of poppy.
    expect(drawnAs(PROMPT.reading)).toBe("go");
    expect(drawnAs(PROMPT.stop)).toBe("stop");
    expect(document.querySelectorAll('[data-kind="go"]')).toHaveLength(1);
  });

  test("test_search_gives_way_to_no_other_button_since_burro_asks_nothing", () => {
    // Search was drawn plain while Burro asked and one press could add what he noticed:
    // that press was then the one that mattered most. Nothing is offered to be pressed
    // now, so Search is cobalt whatever the search holds, and nothing tells it otherwise.
    const source = readFileSync(path.join(__dirname, "PromptBox.tsx"), "utf8");

    expect(source).not.toMatch(/yields/);
    expect(source.match(/kind="go"/g)).toHaveLength(1);
    show({ open: true, onStartAgain: jest.fn() });
    const search = screen.getByRole("button", { name: PROMPT.submit });
    expect(drawnAs(PROMPT.submit)).toBe("go");
    expect(search).toHaveAttribute("type", "submit");
    expect(search).not.toHaveAttribute("aria-pressed");
    expect(search).not.toHaveAttribute("aria-disabled");
  });

  test("test_every_button_of_the_box_is_native_and_as_large_as_a_main_control", () => {
    const { container } = showWithExamples({ open: true, onStartAgain: jest.fn() });
    const buttons = [...container.querySelectorAll("button")];

    expect(buttons.length).toBe(2 + EXAMPLES.length);
    expect(buttons.filter((button) => !button.classList.contains("target"))).toEqual([]);
    expect(container.querySelectorAll("[role='button'], [onclick]")).toHaveLength(0);
  });

  test("test_stop_and_start_again_are_one_button_in_one_place_as_they_were", () => {
    const { rerender, onSubmit, onStop } = show({ open: true, busy: true, onStartAgain: jest.fn() });
    const stop = screen.getByRole("button", { name: PROMPT.stop });

    rerender(<PromptBox maxText={600} busy={false} onSubmit={onSubmit} onStop={onStop} open onStartAgain={jest.fn()} />);

    expect(screen.getByRole("button", { name: PROMPT.startAgain })).toBe(stop);
  });

  test("test_the_label_is_a_short_label_in_the_face_of_names_and_what_is_typed_is_in_the_face_of_sentences", () => {
    expect(setsOf(".label").get("font")).toBe("400 var(--name-2) / 1.1 var(--font-name)");
    expect(setsOf(".label").get("font-synthesis")).toBe("none");
    // The field takes the face of the page, which is the face of sentences, and names no other.
    expect(setsOf(".box").has("font")).toBe(false);
    expect(setsOf(".box").has("font-family")).toBe(false);
    expect(setsOf(".box").get("color")).toBe("var(--ink)");
  });

  test("test_nothing_that_holds_words_has_a_fixed_height", () => {
    const fixed = RULES.filter((rule) => rule.sets.has("height") || rule.sets.has("max-height"));

    // But the carrot, which is a drawing and holds no word.
    expect(fixed.map((rule) => rule.selector)).toEqual([".example::before"]);
  });

  test("test_a_refusal_is_said_in_ink_with_a_mark_of_poppy_beside_it", () => {
    const problem = setsOf(".problem");

    expect(problem.get("color")).toBe("var(--error)");
    expect(problem.get("border-inline-start")).toBe("calc(var(--px) * 2) solid var(--error-edge)");
  });
});

describe("the picture of the box in hand", () => {
  test("test_it_is_asked_for_with_the_page_so_that_the_box_has_its_edge_at_the_first_press_in_it", () => {
    // Seen on a phone: the picture of a box in hand was asked for at the first press in the
    // box, and not with the page. Until it had come the box was drawn with no edge at all,
    // for as long as the picture took on a slow line. It is laid as a ground of no size,
    // which is never seen, by what stands in the box: the box itself is given no ground.
    const form = setsOf(".form");

    expect(form.get("background-image")).toBe("var(--frame-box-on)");
    expect(form.get("background-size")).toBe("0 0");
    expect(form.get("background-repeat")).toBe("no-repeat");
    expect([...setsOf(".prompt").keys()].filter((property) => /^background/.test(property))).toEqual([]);
    // The box is the box in hand while it is typed in, and the box at rest else.
    render(<PromptBox maxText={600} busy={false} onSubmit={jest.fn()} onStop={jest.fn()} />);
    const frame = () => box().closest("[data-kind]");
    expect(frame()).toHaveAttribute("data-kind", "box");
    act(() => box().focus());
    expect(frame()).toHaveAttribute("data-kind", "box-on");
  });
});

describe("the examples, as the look draws them", () => {
  test("test_the_examples_stand_in_a_box_under_their_heading_as_they_did", () => {
    render(<Examples onUse={jest.fn()} />);
    const part = screen.getByRole("region", { name: PROMPT.examplesTitle });

    expect(part).toHaveAttribute("data-kind", "box");
    expect(within(part).getByRole("heading", { name: PROMPT.examplesTitle })).toBeInTheDocument();
    expect(within(part).getAllByRole("button").map((button) => button.textContent)).toEqual([...EXAMPLES]);
  });

  test("test_what_an_example_does_is_said_once_of_them_all_and_not_again_of_each", () => {
    // Heard by keyboard: each of the three examples was described by the same two sentences,
    // so they were heard three times over. They are said once, of the examples as a whole,
    // and stand before the first of them where they are read.
    render(<Examples onUse={jest.fn()} />);
    const part = screen.getByRole("region", { name: PROMPT.examplesTitle });
    const said = within(part).getByText(PROMPT.examplesHint);

    expect(part).toHaveAccessibleDescription(PROMPT.examplesHint);
    for (const button of within(part).getAllByRole("button")) {
      expect(button).toHaveAccessibleName(button.textContent ?? "");
      expect(button).not.toHaveAttribute("aria-describedby");
    }
    const [first] = within(part).getAllByRole("button");
    expect(Boolean(said.compareDocumentPosition(first as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
    expect(said).not.toHaveClass("visually-hidden");
  });

  test("test_under_the_helper_that_offers_one_their_heading_is_kept_for_a_screen_reader_and_not_drawn", () => {
    // Seen in a browser: "Examples" stood directly under "Try an example", and read as said
    // twice. The helper does not name them in their own word, so the heading is kept: it is
    // what names them to whoever hears the page.
    render(
      <Helpers
        label="Other ways to start"
        helpers={[{ id: "example", label: HELPERS.example, children: <Examples onUse={jest.fn()} /> }]}
        open="example"
        onOpen={() => undefined}
      />,
    );
    const part = screen.getByRole("region", { name: PROMPT.examplesTitle });
    const heading = within(part).getByRole("heading", { level: 2, name: PROMPT.examplesTitle });

    expect(heading).toHaveClass("visually-hidden");
    expect(heading).not.toHaveClass("examplesTitle");
    expect(part).toHaveAttribute("aria-labelledby", heading.id);
    // What an example does is said where it can be seen, as it was.
    expect(within(part).getByText(PROMPT.examplesHint)).not.toHaveClass("visually-hidden");
    expect(within(part).getAllByRole("button").map((button) => button.textContent)).toEqual([...EXAMPLES]);
  });

  test("test_the_carrot_lies_beside_the_example_in_hand_and_its_room_stands_before_every_one", () => {
    const { container } = render(<Examples onUse={jest.fn()} />);
    const list = container.querySelector("ul") as HTMLElement;

    expect(list.style.getPropertyValue("--carrot")).toBe('url("/art/ui-carrot.png")');
    expect([list.style.getPropertyValue("--carrot-w"), list.style.getPropertyValue("--carrot-h")]).toEqual(["16", "9"]);
    // Its room is the room of every example, always: nothing moves when it comes or goes.
    expect(setsOf(".example").get("padding")).toContain("calc(var(--px) * (var(--carrot-w) + 6))");
    expect(setsOf(".example::before").has("background")).toBe(false);
    const inHand = RULES.filter((rule) => /^\.example:(focus-visible|hover)/.test(rule.selector));
    expect(inHand.map((rule) => rule.selector).sort()).toEqual([
      ".example:focus-visible",
      ".example:focus-visible::before",
      ".example:hover",
      ".example:hover::before",
    ]);
    // In hand it is drawn otherwise, and is where it was and as large.
    expect([...new Set(inHand.flatMap((rule) => [...rule.sets.keys()]))].sort()).toEqual(["background", "background-color", "color"]);
    // A finger cannot stand over a thing without pressing it, so nothing is drawn for one that does.
    expect(inHand.filter((rule) => /hover/.test(rule.selector)).map((rule) => rule.under)).toEqual([
      "@media (hover: hover) and (pointer: fine)",
      "@media (hover: hover) and (pointer: fine)",
    ]);
  });

  test("test_the_examples_have_no_accessibility_fault", async () => {
    const { container } = render(<Examples onUse={jest.fn()} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the box on a narrow screen, and with larger text", () => {
  const narrow = RULES.filter((rule) => rule.under === "@media (max-width: 23rem)");

  test("test_where_the_field_and_two_buttons_have_no_room_side_by_side_the_buttons_stand_under_the_field", () => {
    // Seen in a browser at 390 px, with text twice as large: the line of the field was
    // 448 px wide, and the page scrolled sideways. The width is in rem, so that it follows
    // the size of text a person has set.
    expect(narrow.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      ['.prompt[data-open="true"] .line', [["grid-template-columns", "minmax(0, 1fr)"]]],
      ['.prompt[data-open="true"] .buttons > *', [["flex", "1 1 auto"]]],
    ]);
  });

  test("test_whether_the_buttons_stand_under_the_field_never_follows_which_buttons_are_drawn", () => {
    // While a sentence is read the two buttons are narrower than Start again and Search. A
    // line that wrapped by what it holds would move them under the press that sent the
    // sentence: so the line is a grid of two columns, and only the width of the screen changes it.
    const line = RULES.filter((rule) => /\.line$/.test(rule.selector));

    expect(line.map((rule) => [rule.under, rule.sets.get("display") ?? null, rule.sets.get("grid-template-columns")])).toEqual([
      [null, "grid", "minmax(6rem, 1fr) auto"],
      ["@media (max-width: 23rem)", null, "minmax(0, 1fr)"],
      // Before a search Search is the one button, and has room beside the field down to 16rem.
      ["@media (max-width: 16rem)", null, "minmax(0, 1fr)"],
    ]);
    expect(RULES.filter((rule) => rule.sets.has("flex-wrap")).map((rule) => rule.selector)).toEqual([".over"]);
  });

  test("test_no_rule_of_the_box_lays_out_a_line_or_a_link_about_how_words_are_handled", () => {
    const sheet = readFileSync(path.join(__dirname, "PromptBox.module.css"), "utf8");

    expect(sheet).not.toMatch(/\.words\b/);
    expect(sheet).not.toMatch(/\.wordsLink\b/);
  });

  test("test_on_a_narrow_screen_an_open_box_keeps_what_it_holds_closer_still", () => {
    // The answer comes first: on a phone the box gives the first result what room it can,
    // so that the first result is whole on the first screen.
    const close = RULES.filter((rule) => rule.under === "@media (max-width: 40rem)" && rule.selector === '.prompt[data-open="true"]');

    expect(close.map((rule) => [...rule.sets])).toEqual([
      [
        ["gap", "var(--space-1)"],
        ["padding", "var(--space-1) var(--space-2)"],
      ],
    ]);
    // Before a search the box has the room it had: no room of it is set for a narrow screen
    // alone. What is said for one there is where the sentences that help are drawn.
    const forANarrowScreen = RULES.filter((rule) => rule.under === "@media (max-width: 40rem)");
    expect(forANarrowScreen.filter((rule) => [...rule.sets.keys()].some((set) => set !== "order")).map((rule) => rule.selector)).toEqual([
      '.prompt[data-open="true"]',
    ]);
    // What is read stands clear of the rule of the box, which lies outside its room.
    expect(setsOf('.prompt[data-open="true"]').get("padding")).toBe("var(--space-2) var(--space-3)");
  });
});

describe("what is laid over the page from inside the box", () => {
  test("test_the_box_stands_over_what_follows_it_so_that_a_list_in_it_is_whole", () => {
    // Seen in a browser, of the box a helper opens: the list of places was laid over what
    // was under it, and the map was drawn over its third place. A box of the look is a layer
    // of its own, and one that comes later on the page is drawn over one that comes before.
    expect(setsOf(".prompt").get("z-index")).toBe("1");
    expect(setsOf(".prompt").has("overflow")).toBe(false);
  });
});
