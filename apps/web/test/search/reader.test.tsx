/**
 * Who reads what is typed, as the search page says it.
 *
 * The page is built ahead of time, and the service may since have been set to
 * another reader. So the page asks the service as it opens, shows what it is
 * told as it was served, and sends no sentence until it has been told.
 */

import { screen, waitFor, within } from "@testing-library/react";

import { FAILURE, PROMPT } from "@/content/search";
import { READER, WORDS_LINE } from "@/content/site";
import { recordedAnswer } from "@/lib/api/recorded";

import { setOnline } from "../support/api";
import { arrived, CANARY, firstSearch, meta, openSearch, promptBox, results } from "../support/search";

const byAModel = recordedAnswer("get_meta", "meta-model-reads").body.data.reader;
const told = () => screen.getByRole("group", { name: READER.label });
const search = () => screen.getByRole("button", { name: PROMPT.submit });

beforeEach(() => setOnline(true));

describe("who reads what is typed", () => {
  test("test_the_line_under_the_box_says_what_the_service_says_now_and_not_what_the_page_was_built_on", async () => {
    // The page was built while the rules read. The service has since been set to a model.
    const api = firstSearch().on("get_meta", "meta-model-reads");
    await openSearch(api);

    expect(meta.data.reader.model_reads).toBe(false);
    expect(byAModel.model_reads).toBe(true);
    expect(told()).toHaveTextContent(WORDS_LINE);
    expect(told()).toHaveTextContent(byAModel.notice);
    expect(told()).not.toHaveTextContent(meta.data.reader.notice);
    // It is said before anything is typed, and nothing of a person was sent to ask for it.
    expect(promptBox()).toHaveValue("");
    expect(api.calls.map((call) => call.sent)).toEqual([null, null]);
  });

  test("test_where_no_model_reads_the_page_says_that_nothing_typed_is_sent_to_one", async () => {
    await openSearch(firstSearch());

    expect(told()).toHaveTextContent(meta.data.reader.notice);
    expect(told()).toHaveTextContent("not sent to a language model");
    expect(within(told()).getByRole("link", { name: PROMPT.wordsLink })).toHaveAttribute("href", "/methods#words");
  });

  test("test_nothing_the_page_was_built_on_is_shown_while_the_service_has_not_said", async () => {
    const api = firstSearch();
    const asked = api.hold("get_meta", "meta-model-reads");
    await openSearch(api);

    expect(told()).toHaveTextContent(READER.checking);
    expect(told()).not.toHaveTextContent(meta.data.reader.notice);

    asked.release();
    await arrived();
    expect(told()).toHaveTextContent(byAModel.notice);
    expect(told()).not.toHaveTextContent(READER.checking);
  });

  test("test_a_sentence_sent_before_the_service_has_said_who_reads_waits_until_it_has", async () => {
    const api = firstSearch();
    const asked = api.hold("get_meta", "meta-model-reads");
    const { user } = await openSearch(api);

    await user.type(promptBox(), `leafy ${CANARY}`);
    await user.click(search());
    await arrived();

    expect(api.callsTo("interpret")).toEqual([]);
    expect(api.calls.some((call) => call.sent?.includes(CANARY))).toBe(false);

    asked.release();
    await waitFor(() => expect(results().length).toBeGreaterThan(0));
    expect(api.callsTo("interpret")).toHaveLength(1);
  });

  test("test_where_the_service_cannot_say_who_reads_the_page_says_so_and_sends_no_sentence", async () => {
    const api = firstSearch().unreachable("get_meta");
    const { user } = await openSearch(api);

    expect(told()).toHaveTextContent(READER.unsaid);
    await user.type(promptBox(), `leafy ${CANARY}`);
    await user.click(search());
    await arrived();

    expect(api.callsTo("interpret")).toEqual([]);
    expect(api.calls.some((call) => call.sent?.includes(CANARY))).toBe(false);
    // The page says that Burro could not be reached. It does not blame the words.
    expect(document.body.textContent?.includes(FAILURE.network)).toBe(true);
    expect(promptBox()).toHaveValue(`leafy ${CANARY}`);
  });
});
