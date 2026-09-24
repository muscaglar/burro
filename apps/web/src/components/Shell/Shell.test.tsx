import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { BANNER, DISAGREES, PREVIEW_BANNER, SITE } from "@/content/site";
import { recordedAnswer } from "@/lib/api/recorded";
import { forgetWhatWasSaid, noteSaid } from "@/lib/api/said";
import { forgetSynthetic, noteSynthetic } from "@/lib/api/synthetic";

import { faultsIn } from "../../../test/support/axe";
import { Shell } from "./Shell";

let pathname = "/";
jest.mock("next/navigation", () => ({ usePathname: () => pathname }));

const { meta } = recordedAnswer("get_meta", "meta").body;
const real = { ...meta, release_id: "lon-2027-01-20-01", synthetic: false };
const preview = { ...real, preview: true };

function page(of = meta) {
  return render(
    <Shell meta={of}>
      <h1>A page</h1>
      <p>What the page says.</p>
    </Shell>,
  );
}

beforeEach(() => {
  pathname = "/";
  forgetSynthetic();
  forgetWhatWasSaid();
});

/** An answer of the API arrives, and says this of its data. */
function anAnswerSays(said: { synthetic: boolean; preview: boolean }) {
  act(() => {
    noteSynthetic(said.synthetic);
    noteSaid(said);
  });
}

describe("what every page has", () => {
  test("test_every_page_says_the_data_is_made_up_while_it_is", () => {
    page();

    expect(screen.getByRole("region", { name: BANNER.label })).toHaveTextContent(BANNER.text);
  });

  test("test_a_page_built_on_real_data_has_no_banner", () => {
    page(real);

    expect(screen.queryByRole("region", { name: BANNER.label })).toBeNull();
  });

  test("test_a_page_built_on_a_preview_of_real_data_says_it_is_a_preview_and_not_that_it_is_made_up", () => {
    const { container } = page(preview);

    expect(screen.getByRole("region", { name: PREVIEW_BANNER.label })).toHaveTextContent(PREVIEW_BANNER.text);
    expect(screen.queryByRole("region", { name: BANNER.label })).toBeNull();
    // It stands where the other banner stands: before everything but the skip link.
    const order = [...container.querySelectorAll("a[href='#main'], section, header, main, footer")];
    expect(order.map((element) => element.tagName.toLowerCase())).toEqual([
      "a",
      "section",
      "header",
      "main",
      "footer",
    ]);
  });

  test("test_a_finished_release_has_no_banner_of_either_kind", () => {
    page(real);

    expect(screen.queryByRole("region", { name: PREVIEW_BANNER.label })).toBeNull();
    expect(screen.queryByRole("region", { name: BANNER.label })).toBeNull();
  });

  test("test_a_made_up_preview_says_both", () => {
    page({ ...meta, preview: true });

    expect(screen.getByRole("region", { name: BANNER.label })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: PREVIEW_BANNER.label })).toBeInTheDocument();
  });

  test("test_the_first_thing_a_keyboard_reaches_skips_to_the_page_itself", async () => {
    page();

    await userEvent.tab();

    const skip = screen.getByRole("link", { name: SITE.skipToContent });
    expect(skip).toHaveFocus();
    expect(skip).toHaveAttribute("href", "#main");
    expect(screen.getByRole("main")).toHaveAttribute("id", "main");
    // A region that is skipped to must be able to take focus.
    expect(screen.getByRole("main")).toHaveAttribute("tabindex", "-1");
  });

  test("test_no_link_of_the_header_or_the_footer_is_fetched_ahead_of_time", () => {
    // Seen in a browser: every page that was opened asked for the three pages about the
    // website four times over, before anyone had pressed a link to one.
    const { container } = page();

    const links = [...container.querySelectorAll<HTMLAnchorElement>("header a[href], footer a[href]")];
    expect(links.length).toBeGreaterThanOrEqual(7);
    expect(links.filter((link) => link.getAttribute("data-prefetch") !== "false").map((link) => link.href)).toEqual(
      [],
    );
  });

  test("test_the_banner_comes_before_everything_but_the_skip_link", () => {
    const { container } = page();

    const order = [...container.querySelectorAll("a[href='#main'], section, header, main, footer")];

    expect(order.map((element) => element.tagName.toLowerCase())).toEqual([
      "a",
      "section",
      "header",
      "main",
      "footer",
    ]);
  });

  test.each(["banner", "contentinfo"] as const)(
    "test_vibes_methods_sources_and_accessibility_are_linked_from_the_%s",
    (landmark) => {
      page();

      const links = within(screen.getByRole(landmark)).getAllByRole("link");

      expect(
        links.map((link) => [link.textContent, link.getAttribute("href")]),
      ).toEqual(
        expect.arrayContaining([
          ["Vibes", "/vibes"],
          ["Methods", "/methods"],
          ["Sources", "/sources"],
          ["Accessibility", "/accessibility"],
        ]),
      );
    },
  );

  test("test_the_name_of_the_site_leads_to_the_search", () => {
    page();

    expect(
      within(screen.getByRole("banner")).getByRole("link", { name: SITE.name }),
    ).toHaveAttribute("href", "/");
  });

  test("test_the_page_being_read_is_marked_in_the_navigation_in_more_than_colour", () => {
    pathname = "/sources";
    page();

    const nav = within(screen.getByRole("navigation", { name: SITE.navLabel }));

    expect(nav.getByRole("link", { name: "Sources" })).toHaveAttribute("aria-current", "page");
    expect(nav.getByRole("link", { name: "Methods" })).not.toHaveAttribute("aria-current");
  });

  test("test_the_footer_names_the_release_and_the_engine_behind_every_figure", () => {
    page();

    const footer = screen.getByRole("contentinfo");
    expect(footer).toHaveTextContent(meta.release_id);
    expect(footer).toHaveTextContent(meta.engine_version);
  });

  test("test_every_link_in_the_shell_takes_a_target_size", () => {
    page();

    for (const landmark of ["banner", "contentinfo"] as const) {
      for (const link of within(screen.getByRole(landmark)).getAllByRole("link")) {
        expect(link).toHaveClass("target");
      }
    }
    expect(screen.getByRole("link", { name: SITE.skipToContent })).toHaveClass("target");
  });

  test("test_the_two_navigations_can_be_told_apart_by_name", () => {
    page();

    const names = screen.getAllByRole("navigation").map((nav) => nav.getAttribute("aria-label"));

    expect(names).toEqual([SITE.navLabel, SITE.footerLabel]);
    expect(new Set(names).size).toBe(2);
  });

  test("test_the_shell_has_no_accessibility_fault", async () => {
    const { container } = page();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("a page read while the service answers with another kind of data than it was built on", () => {
  const WHAT_THE_PAGE_SAYS = "What the page says.";

  test("test_a_page_built_on_made_up_data_shows_no_real_figure_under_the_words_made_up", () => {
    // Read in the code, by a checker: a website built while the service held the made-up
    // release, and read once it held a preview of real data, said "made-up" over London.
    page(meta);
    expect(screen.getByRole("main")).toHaveTextContent(WHAT_THE_PAGE_SAYS);

    anAnswerSays({ synthetic: false, preview: true });

    const main = screen.getByRole("main");
    expect(main).not.toHaveTextContent(WHAT_THE_PAGE_SAYS);
    expect(within(main).getByRole("alert")).toHaveTextContent(DISAGREES.text);
    expect(screen.queryByRole("heading", { name: "A page" })).toBeNull();
  });

  test("test_a_page_built_on_real_data_shows_no_made_up_figure_as_real", () => {
    page(preview);

    anAnswerSays({ synthetic: true, preview: true });

    expect(screen.getByRole("main")).not.toHaveTextContent(WHAT_THE_PAGE_SAYS);
    expect(screen.getByRole("alert")).toHaveTextContent(DISAGREES.text);
    expect(screen.getByRole("region", { name: BANNER.label })).toBeInTheDocument();
  });

  test("test_a_page_built_on_a_finished_release_says_so_when_an_answer_is_of_a_preview", () => {
    page(real);
    expect(screen.queryByRole("region", { name: PREVIEW_BANNER.label })).toBeNull();

    anAnswerSays({ synthetic: false, preview: true });

    expect(screen.getByRole("region", { name: PREVIEW_BANNER.label })).toHaveTextContent(
      PREVIEW_BANNER.text,
    );
    expect(screen.getByRole("main")).not.toHaveTextContent(WHAT_THE_PAGE_SAYS);
    expect(screen.getByRole("alert")).toHaveTextContent(DISAGREES.text);
  });

  test("test_a_page_built_on_a_preview_shows_nothing_when_an_answer_is_of_a_finished_release", () => {
    page(preview);

    anAnswerSays({ synthetic: false, preview: false });

    expect(screen.getByRole("main")).not.toHaveTextContent(WHAT_THE_PAGE_SAYS);
    // The banner stays: the page was built on a preview, and says so still.
    expect(screen.getByRole("region", { name: PREVIEW_BANNER.label })).toBeInTheDocument();
  });

  test.each([
    ["made up", meta, { synthetic: true, preview: false }],
    ["a preview of real data", preview, { synthetic: false, preview: true }],
    ["finished", real, { synthetic: false, preview: false }],
  ])("test_a_page_and_an_answer_that_are_both_%s_show_the_page", (_, built, said) => {
    page(built);

    anAnswerSays(said);

    expect(screen.getByRole("main")).toHaveTextContent(WHAT_THE_PAGE_SAYS);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("test_a_release_that_moved_on_to_another_of_the_same_kind_changes_nothing_here", () => {
    // Every answer names its release, and the search keeps what each release made apart.
    page(preview);

    anAnswerSays({ synthetic: false, preview: true });
    anAnswerSays({ synthetic: false, preview: true });

    expect(screen.getByRole("main")).toHaveTextContent(WHAT_THE_PAGE_SAYS);
  });

  test("test_what_is_said_in_place_of_the_page_holds_no_figure_and_names_no_place", () => {
    expect(/\d/.test(DISAGREES.text)).toBe(false);
    expect(DISAGREES.text.includes("London")).toBe(false);
  });

  test("test_what_is_said_in_place_of_the_page_has_no_accessibility_fault", async () => {
    const { container } = page(meta);

    anAnswerSays({ synthetic: false, preview: true });

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});
