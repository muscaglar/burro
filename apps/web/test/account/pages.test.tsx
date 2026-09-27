/**
 * The four pages of accounts, each as a person finds it: inside the shell, under the
 * banner. With accounts off each answers that there is no such page. With them on each is
 * held to what every page of the website is held to.
 */

import { readdirSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import type { Metadata } from "next";
import type { ReactElement } from "react";

import * as account from "@/app/account/[[...rest]]/page";
import * as confirm from "@/app/sign-in/confirm/[[...rest]]/page";
import * as signIn from "@/app/sign-in/[[...rest]]/page";
import * as sent from "@/app/sign-in/sent/[[...rest]]/page";
import { Shell } from "@/components/Shell/Shell";
import { ACCOUNT, ACCOUNT_NAV, CONFIRM, SENT, SIGN_IN } from "@/content/account";
import { BANNER, NOT_FOUND, SITE } from "@/content/site";
import { forgetAsked } from "@/lib/account/asked";
import { ACCOUNT_PAGES } from "@/lib/account/paths";
import { forgetWho } from "@/lib/account/who";
import { recordedAnswer } from "@/lib/api/recorded";
import { KEEP_OUT, ONE_PERSONS } from "@/lib/indexing";

import { arrived, EVERY_ROUTE, held, standInAccounts } from "../support/account";
import { faultsIn } from "../support/axe";

let pathname = "/";
jest.mock("next/navigation", () => ({
  ...jest.requireActual<typeof import("next/navigation")>("next/navigation"),
  usePathname: () => pathname,
  useRouter: () => ({ push: () => undefined }),
}));

const { meta } = recordedAnswer("get_meta", "meta").body;
const APP = path.resolve(__dirname, "..", "..", "src", "app");

/** What the file of a page hands to the framework. */
interface Built {
  readonly default: () => ReactElement | Promise<ReactElement>;
  readonly generateMetadata: () => Metadata;
  readonly generateStaticParams: () => { rest: string[] }[];
  readonly dynamicParams: boolean;
}

interface Page {
  readonly at: string;
  readonly built: Built;
  readonly draws: () => ReactElement | Promise<ReactElement>;
  readonly describes: () => Metadata;
  readonly title: string;
  readonly heading: string;
}

const page = (at: string, built: Built, title: string, heading: string): Page => ({
  at,
  built,
  draws: built.default,
  describes: built.generateMetadata,
  title,
  heading,
});

const PAGES: readonly Page[] = [
  page("/sign-in", signIn, SIGN_IN.pageTitle, SIGN_IN.title),
  page("/sign-in/sent", sent, SENT.pageTitle, SENT.title),
  page("/sign-in/confirm", confirm, CONFIRM.pageTitle, CONFIRM.none.title),
  page("/account", account, ACCOUNT.pageTitle, ACCOUNT.out.title),
];

/** What a page does where there is no such page: it stops, as the framework has a page stop that is not there. */
async function stopsAs(draws: Page["draws"]): Promise<string> {
  try {
    await draws();
    return "it was drawn";
  } catch (stopped) {
    return String((stopped as { digest?: unknown }).digest ?? stopped);
  }
}

async function show(page: Page) {
  pathname = page.at;
  const view = render(<Shell meta={meta}>{await page.draws()}</Shell>);
  await arrived();
  return view;
}

beforeEach(() => {
  pathname = "/";
  forgetWho();
  forgetAsked();
  delete process.env.NEXT_PUBLIC_BURRO_ACCOUNTS;
  // Nobody is signed in, and the service says so.
  globalThis.fetch = standInAccounts(held({ signedIn: false })).fetch;
});

afterAll(() => {
  delete process.env.NEXT_PUBLIC_BURRO_ACCOUNTS;
});

/** Every page under a folder of the app, by the address it is built at. */
function pagesUnder(folder: string, found: string[] = []): string[] {
  for (const entry of readdirSync(folder, { withFileTypes: true })) {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) pagesUnder(file, found);
    else if (entry.name === "page.tsx") found.push(path.relative(APP, path.dirname(file)));
  }
  return found;
}

describe("the pages of accounts", () => {
  test("test_they_are_four_and_each_has_a_fixed_address", () => {
    expect(PAGES.map((page) => page.at)).toEqual(ACCOUNT_PAGES);
    expect(ACCOUNT_PAGES).toEqual(["/sign-in", "/sign-in/sent", "/sign-in/confirm", "/account"]);
  });

  test("test_each_stands_in_a_folder_that_is_built_only_where_accounts_are_on", () => {
    // A page that stood at its address plainly would be built with accounts off, and would
    // answer with an empty frame: `check:pages` reads it, and finds it wanting.
    const standing = [...pagesUnder(path.join(APP, "sign-in")), ...pagesUnder(path.join(APP, "account"))].sort();

    expect(standing).toEqual(
      ["account", "sign-in", "sign-in/confirm", "sign-in/sent"].map((at) => path.join(at, "[[...rest]]")).sort(),
    );
  });
});

describe.each(PAGES)("$at, with accounts off", (page) => {
  test("test_no_page_is_built_at_the_address_and_none_is_drawn_when_it_is_asked_for", () => {
    // Nothing is built, and nothing is drawn that was not built: the address is answered
    // as any address is that the website has nothing at, by the page that says so.
    expect(page.built.generateStaticParams()).toEqual([]);
    expect(page.built.dynamicParams).toBe(false);
  });

  test("test_the_page_answers_that_there_is_no_such_page_if_it_is_drawn_all_the_same", async () => {
    expect(await stopsAs(page.draws)).toMatch(/^NEXT_HTTP_ERROR_FALLBACK;404$/);
  });

  test.each(["", "off", "true", "1", "ON"])("test_it_is_off_unless_the_one_setting_says_on: %s", async (value) => {
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = value;

    expect(await stopsAs(page.draws)).toMatch(/404/);
  });

  test("test_it_says_of_itself_what_a_page_that_is_not_there_says", () => {
    const said = page.describes();

    expect(said.title).toBe(NOT_FOUND.title);
    expect(said.description).toBeUndefined();
    expect(said.robots).toEqual(KEEP_OUT);
  });

  test("test_nothing_is_asked_of_the_service", async () => {
    const asked = jest.fn(() => Promise.reject(new Error("Nothing may be asked with accounts off.")));
    globalThis.fetch = asked as unknown as typeof fetch;

    await stopsAs(page.draws);
    await arrived();

    expect(asked).not.toHaveBeenCalled();
  });
});

describe.each(PAGES)("$at, with accounts on", (page) => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = "on";
  });

  test("test_one_page_is_built_at_the_address_and_nothing_is_drawn_at_an_address_that_follows_it", () => {
    expect(page.built.generateStaticParams()).toEqual([{ rest: [] }]);
    expect(page.built.dynamicParams).toBe(false);
  });

  test("test_the_page_has_one_main_heading_which_says_what_it_is", async () => {
    await show(page);

    expect(screen.getAllByRole("heading", { level: 1 }).map((heading) => heading.textContent)).toEqual([page.heading]);
  });

  test("test_the_page_carries_the_banner_that_says_the_data_is_made_up", async () => {
    await show(page);

    expect(screen.getByRole("region", { name: BANNER.label })).toHaveTextContent(BANNER.text);
  });

  test("test_the_page_has_no_accessibility_fault", async () => {
    const { container } = await show(page);

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });

  test("test_everything_on_the_page_can_be_reached_by_keyboard", async () => {
    const { container } = await show(page);

    const controls = [...container.querySelectorAll("main a, main button, main input, main select, main textarea")];
    const unreachable = controls.filter(
      (control) => control.getAttribute("tabindex") === "-1" || (control.tagName === "A" && !control.hasAttribute("href")) || control.hasAttribute("disabled"),
    );

    expect(controls.length).toBeGreaterThan(0);
    expect(unreachable).toEqual([]);
    expect(container.querySelectorAll("main [role='button'], main [role='link'], main [onclick]")).toHaveLength(0);
    // Every control takes the size of one.
    expect(controls.filter((control) => !control.matches(".target, .target-min")).map((control) => control.textContent)).toEqual([]);
  });

  test("test_the_page_stands_boxes_of_its_own_on_the_grass_and_nothing_of_it_is_read_there", async () => {
    const { container } = await show(page);
    const main = container.querySelector("main") as HTMLElement;

    expect(main.children).toHaveLength(1);
    expect(main.firstElementChild).toHaveAttribute("data-dressed");
    // What the page holds is boxes of the kit, and nothing stands loose beside them.
    const loose = [...(main.firstElementChild?.children ?? [])].filter((one) => one.getAttribute("data-kind") !== "box");
    expect(loose.map((one) => one.tagName)).toEqual([]);
  });

  test("test_nothing_on_the_page_comes_from_another_origin", async () => {
    const { container } = await show(page);

    expect([...container.querySelectorAll("[src], link[href], [srcset], [poster]")]).toEqual([]);
    const leads = [...container.querySelectorAll<HTMLAnchorElement>("main a[href]")].map((link) => link.getAttribute("href") ?? "");
    expect(leads.filter((href) => !/^\/([a-z-]+(\/[a-z-]+)*)?$/.test(href))).toEqual([]);
  });

  test("test_no_link_of_the_page_is_fetched_ahead_of_time", async () => {
    const { container } = await show(page);

    const ahead = [...container.querySelectorAll<HTMLAnchorElement>("main a[href]")].filter((link) => link.getAttribute("data-prefetch") !== "false");
    expect(ahead.map((link) => link.getAttribute("href"))).toEqual([]);
  });

  test("test_the_entry_of_the_name_board_says_that_this_is_the_page_being_read_where_it_is_of_it", async () => {
    await show(page);

    const entry = within(screen.getByRole("banner")).getByRole("link", { name: ACCOUNT_NAV.signIn });
    expect(entry.getAttribute("aria-current")).toBe(page.at === "/account" ? null : "page");
  });

  test("test_it_says_of_itself_what_it_is_and_asks_to_be_left_out_by_a_search_engine", () => {
    const said = page.describes();

    expect(said.title).toBe(page.title);
    expect(String(said.description).length).toBeGreaterThan(20);
    // It is one person's way in, or one person's account: never a page to index.
    expect(said.robots).toEqual(KEEP_OUT);
  });

  test("test_the_page_is_built_the_same_for_everybody_and_holds_nothing_of_anybody", async () => {
    // Drawn twice, for a service that holds two different people: what is built is the same.
    const draw = async (email: string) => {
      forgetWho();
      globalThis.fetch = standInAccounts(held({ signedIn: false, email })).fetch;
      const { renderToStaticMarkup } = await import("react-dom/server");
      return renderToStaticMarkup(<Shell meta={meta}>{await page.draws()}</Shell>);
    };

    const [one, other] = [await draw("one@example.org"), await draw("other@example.org")];

    expect(one).toBe(other);
    expect(one).not.toMatch(/@example\.org/);
  });
});

describe("what each page is called", () => {
  test("test_no_two_of_them_bear_one_title_and_none_bears_the_title_of_another_page_of_the_website", () => {
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = "on";
    const titles = PAGES.map((page) => String(page.describes().title));

    expect(new Set(titles).size).toBe(PAGES.length);
    expect(titles).toEqual(["Sign in", "Check your email", "Finish signing in", "Your account"]);
    // The pages that were there before accounts, by what each is called in the name board and the foot.
    for (const taken of [SITE.name, ...Object.values(SITE.nav), NOT_FOUND.title]) expect(titles).not.toContain(taken);
  });
});

describe("the page a link opens", () => {
  test("test_it_sends_no_referrer", () => {
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = "on";

    expect(confirm.generateMetadata().referrer).toBe("no-referrer");
  });
});

describe("what a search engine is told of the pages of accounts", () => {
  test("test_every_one_of_them_asks_to_be_left_out_in_its_own_markup_whatever_the_rule_of_the_website_says", () => {
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = "on";

    for (const page of PAGES) expect([page.at, page.describes().robots]).toEqual([page.at, KEEP_OUT]);
  });

  test("test_every_one_of_them_carries_the_header_too_and_so_does_what_the_website_passes_on", () => {
    // As Next reads a source: a name, and after it as many parts as there are, or none.
    const covers = (source: string, at: string) =>
      source.endsWith("/:path*") ? at === source.slice(0, -"/:path*".length) || at.startsWith(source.slice(0, -":path*".length)) : at === source;
    const carried = (at: string) => ONE_PERSONS.some((source) => covers(source, at));

    for (const page of PAGES) expect([page.at, carried(page.at)]).toEqual([page.at, true]);
    for (const { path: route } of EVERY_ROUTE) expect([route, carried(route)]).toEqual([route, true]);
    // And no page that a search engine may find is among them.
    for (const at of ["/", "/vibes", "/methods", "/sources", "/synthetic/alderwick"]) {
      expect([at, carried(at)]).toEqual([at, false]);
    }
  });
});
