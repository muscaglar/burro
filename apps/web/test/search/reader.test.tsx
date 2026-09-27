/**
 * Who reads what is typed, and what the search page does about it.
 *
 * The page is built ahead of time, and the service may since have been set to
 * another reader. So the page asks the service as it opens, and sends no
 * sentence until it has been told.
 *
 * It says nothing of it beside the box. The founder walked the page and had
 * the lines under the box go, with the link beside them: the page of methods
 * says who reads what is typed, and the foot of every page leads to it. So
 * what is held of the link is held of the search page, and the foot that the
 * page stands over is held to lead there, once.
 */

import { screen, waitFor, within } from "@testing-library/react";

import { METHODS } from "@/content/methods";
import { FAILURE, PROMPT } from "@/content/search";
import { WORDS_LINE } from "@/content/site";
import { recordedAnswer } from "@/lib/api/recorded";
import { paths } from "@/lib/paths";

import { setOnline, type StandIn } from "../support/api";
import { arrived, CANARY, firstSearch, meta, openSearch, promptBox, results } from "../support/search";

const byAModel = recordedAnswer("get_meta", "meta-model-reads").body.data.reader;
const withSettings = recordedAnswer("get_meta", "meta-model-reads-with-settings").body.data.reader;
const search = () => screen.getByRole("button", { name: PROMPT.submit });

/** Every line that stood under the box, in every form it took. */
const LINES_THAT_WENT = [
  WORDS_LINE,
  meta.data.reader.notice,
  byAModel.notice,
  withSettings.notice,
];

/** The search page, from its heading to its map: all of it but the shell it stands in. */
const thePage = () => document.querySelector<HTMLElement>("[data-search]");
/** Where what is said of what a person types stands, among the methods. */
const THE_WORDS = paths.methods("words");

function saysNothingOfWhoReads(): void {
  const page = thePage();
  const said = page?.textContent ?? "";
  expect(said.length).toBeGreaterThan(0);
  for (const line of LINES_THAT_WENT) expect(said.includes(line)).toBe(false);
  expect(said).not.toMatch(/What you type is (sent|read)/);
  expect(said).not.toMatch(/language model/i);
  expect(said).not.toMatch(/who (else )?reads what you type/i);
  // No link of the search page leads to how words are handled, by its name or by where it leads.
  expect(within(page as HTMLElement).queryAllByRole("link", { name: /words are handled/i })).toEqual([]);
  expect(page?.querySelectorAll(`a[href$="${THE_WORDS}"]`)).toHaveLength(0);
  // The foot of the page leads there, as the foot of every page does, and nothing else of
  // what the page stands in: what went from beside the box is one press away, and is said
  // once. A result has a foot of its own, so the foot of the page is the one outside `main`.
  const leads = screen.getAllByRole("link", { name: new RegExp(METHODS.words.title) });
  expect(
    leads.map((link) => [link.closest("main") === null && link.closest("footer") !== null, link.getAttribute("href")]),
  ).toEqual([[true, THE_WORDS]]);
}

beforeEach(() => setOnline(true));

describe("who reads what is typed", () => {
  test("test_the_page_asks_the_service_who_reads_as_it_opens_and_sends_nothing_of_a_person_to_ask", async () => {
    // The page was built while the rules read. The service has since been set to a model.
    const api = firstSearch().on("get_meta", "meta-model-reads");
    await openSearch(api);

    expect(meta.data.reader.model_reads).toBe(false);
    expect(byAModel.model_reads).toBe(true);
    expect(api.callsTo("get_meta")).toHaveLength(1);
    expect(promptBox()).toHaveValue("");
    expect(api.calls.map((call) => call.sent)).toEqual([null, null]);
  });

  test.each<[string, (api: StandIn) => StandIn]>([
    ["where the rules read", (api) => api],
    ["where a language model reads", (api) => api.on("get_meta", "meta-model-reads")],
    ["where the settings go with the words", (api) => api.on("get_meta", "meta-model-reads-with-settings")],
    ["where the service cannot say", (api) => api.unreachable("get_meta")],
  ])("test_nothing_beside_the_box_says_who_reads_before_a_search_or_after_one: %s", async (_, set) => {
    const { user } = await openSearch(set(firstSearch()));

    saysNothingOfWhoReads();

    await user.type(promptBox(), "leafy");
    await user.click(search());
    await arrived();

    saysNothingOfWhoReads();
  });

  test("test_nothing_beside_the_box_says_that_the_service_is_being_asked_while_it_has_not_said", async () => {
    const api = firstSearch();
    const asked = api.hold("get_meta", "meta-model-reads");
    await openSearch(api);

    saysNothingOfWhoReads();

    asked.release();
    await arrived();
    saysNothingOfWhoReads();
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

  test("test_where_the_service_cannot_say_who_reads_no_sentence_is_sent_and_the_page_says_burro_could_not_be_reached", async () => {
    const api = firstSearch().unreachable("get_meta");
    const { user } = await openSearch(api);

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
