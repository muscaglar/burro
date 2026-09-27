/**
 * The page that says a link to sign in was sent. It says the same whether or not the
 * address has an account, shows the address to the person who typed it, and sends nothing.
 */

import { render, screen } from "@testing-library/react";

import { SENT } from "@/content/account";
import { forgetAsked, noteAsked } from "@/lib/account/asked";
import { accountPaths } from "@/lib/account/paths";

import { faultsIn } from "../../../test/support/axe";
import { watch } from "../../../test/support/watch";
import { Sent } from "./Sent";

jest.mock("next/navigation", () => ({ usePathname: () => "/sign-in/sent" }));

const CANARY = "zqxcanary7431";

beforeEach(() => forgetAsked());

describe("the page that says a link was sent", () => {
  test("test_it_says_where_the_link_was_sent_and_how_long_it_works_for_as_the_service_said", () => {
    noteAsked({ email: "rowan.ashdown@example.org", minutes: 15 });
    render(<Sent />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(SENT.title);
    expect(screen.getByText(SENT.to("rowan.ashdown@example.org"))).toBeInTheDocument();
    expect(screen.getByText(SENT.lasts(15))).toBeInTheDocument();
    expect(SENT.lasts(15)).toMatch(/only for 15 minutes/);
    expect(SENT.lasts(1)).toMatch(/only for 1 minute,/);
  });

  test("test_what_it_says_does_not_tell_whether_the_address_has_an_account", () => {
    // It is handed the address and how long a link lasts, and nothing else: so it has
    // nothing to tell one address from another by.
    expect(SENT.to("a@example.org").replace("a@example.org", "")).toBe(SENT.to("b@example.org").replace("b@example.org", ""));
    expect(SENT.to("a@example.org")).toMatch(/^If a@example\.org can receive email, a sign-in link is on its way to it\.$/);
    expect(Object.values(SENT).filter((one) => typeof one === "string").join(" ")).not.toMatch(/\b(new account|no account|already have)\b/i);
  });

  test("test_loaded_again_it_holds_no_address_and_names_none", () => {
    render(<Sent />);

    expect(screen.getByText(SENT.toTheAddress)).toBeInTheDocument();
    expect(screen.getByText(SENT.lastsAWhile)).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/@/);
  });

  test("test_it_says_to_open_the_link_in_this_browser_and_that_a_search_is_not_lost", () => {
    render(<Sent />);

    expect(screen.getByText(SENT.here)).toBeInTheDocument();
    expect(screen.getByText(SENT.stays)).toBeInTheDocument();
    expect(screen.getByText(SENT.late)).toBeInTheDocument();
    expect(SENT.stays).toMatch(/it will still be here when you come back to this tab/);
    // The way back to what a person was doing is the button that matters most.
    expect(screen.getByRole("link", { name: SENT.back })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: SENT.again })).toHaveAttribute("href", accountPaths.signIn());
  });

  test("test_where_a_press_led_here_the_heading_takes_the_focus_and_opened_another_way_nothing_does", () => {
    const another = render(<Sent />);
    expect(document.body).toHaveFocus();
    another.unmount();

    noteAsked({ email: "rowan.ashdown@example.org", minutes: 15 });
    render(<Sent />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveFocus();
  });

  test("test_the_address_is_drawn_as_words_and_is_in_no_address_no_attribute_and_nothing_the_browser_keeps", () => {
    const watching = watch();
    try {
      noteAsked({ email: `${CANARY}@example.org`, minutes: 15 });
      const at = window.location.href;
      const { container } = render(<Sent />);

      expect(container.textContent?.includes(CANARY)).toBe(true);
      const attributes = [...document.querySelectorAll("*")].flatMap((one) => [...one.attributes].map((attribute) => attribute.value));
      expect(attributes.filter((value) => value.includes(CANARY))).toEqual([]);
      expect([watching.storage, watching.console, watching.history]).toEqual([[], [], []]);
      expect(watching.everythingOutsideThePage().includes(CANARY)).toBe(false);
      expect([window.location.href === at, document.title.includes(CANARY)]).toEqual([true, false]);
    } finally {
      watching.stop();
    }
  });

  test("test_the_page_has_no_accessibility_fault_with_an_address_and_without", async () => {
    const without = render(<Sent />);
    expect(await faultsIn(without.container)).toEqual([]);
    without.unmount();

    noteAsked({ email: "rowan.ashdown@example.org", minutes: 15 });
    const { container } = render(<Sent />);
    expect(await faultsIn(container)).toEqual([]);
  });
});
