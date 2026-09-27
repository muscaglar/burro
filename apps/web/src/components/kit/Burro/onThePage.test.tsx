/**
 * He is one rabbit. What every page stands in draws him, in the name board and over the
 * foot, and the page draws him too: beside its heading, and where he hops.
 * Where the page draws him, what every page stands in does not.
 *
 * A style sheet says so first, for a page that has not yet run and for one that never
 * runs: it lays nothing of him out in the board or over the foot where the page holds
 * him. jsdom reads no style sheet. What is held here is the second hand: once the page
 * runs, he is in the page once.
 */

import { act, render, screen } from "@testing-library/react";

import { Burro } from "./Burro";
import { BurroOfEveryPage } from "./OfEveryPage";

const his = (within: string) => [...document.querySelectorAll(`${within} [data-pose]`)].map((he) => he.getAttribute("data-pose"));

function Page({ draws }: { readonly draws: "sits" | "hops" | null }) {
  return (
    <>
      <header>
        <BurroOfEveryPage />
      </header>
      <main>{draws === null ? <p>The answer</p> : <Burro pose={draws} />}</main>
      <footer>
        <BurroOfEveryPage />
      </footer>
    </>
  );
}

afterEach(() => {
  jest.restoreAllMocks();
  Reflect.deleteProperty(globalThis, "ResizeObserver");
});

describe("the rabbit of every page, where the page draws him too", () => {
  test("test_where_the_page_draws_none_he_is_drawn_by_what_every_page_stands_in_seen_from_his_back_up", () => {
    render(<Page draws={null} />);

    expect([his("header"), his("main"), his("footer")]).toEqual([["sits"], [], ["sits"]]);
    for (const he of document.querySelectorAll("[data-pose]")) expect(he).toHaveAttribute("data-peeps", "true");
    // He stirs in both, and nothing stands by him to be pressed.
    for (const he of document.querySelectorAll("[data-pose] > [aria-hidden]")) expect(he).toHaveAttribute("data-moves", "true");
    expect(screen.queryAllByRole("button")).toEqual([]);
  });

  test.each(["sits", "hops"] as const)("test_where_the_page_draws_him_he_is_in_the_page_once: %s", (pose) => {
    render(<Page draws={pose} />);

    expect([his("header"), his("main"), his("footer")]).toEqual([[], [pose], []]);
    // Nothing of him is heard or reached, wherever he is drawn.
    expect(screen.queryAllByRole("button")).toEqual([]);
    expect(document.querySelector("[data-pose]")?.closest("[aria-hidden='true']")).not.toBeNull();
  });

  test("test_he_comes_to_the_board_as_the_page_lets_him_go_and_leaves_it_as_the_page_draws_him_again", () => {
    const { rerender } = render(<Page draws="sits" />);
    expect([his("header"), his("main"), his("footer")]).toEqual([[], ["sits"], []]);

    // A search is read: he hops on the page. The answer is in: the page draws him no more.
    rerender(<Page draws="hops" />);
    expect([his("header"), his("main"), his("footer")]).toEqual([[], ["hops"], []]);
    rerender(<Page draws={null} />);
    expect([his("header"), his("main"), his("footer")]).toEqual([["sits"], [], ["sits"]]);
    // Start again: he sits beside the heading, and nowhere else.
    rerender(<Page draws="sits" />);
    expect([his("header"), his("main"), his("footer")]).toEqual([[], ["sits"], []]);
  });

  test("test_a_rabbit_of_the_page_that_a_browser_does_not_draw_is_not_counted", () => {
    // A page may hold him where its style sheet does not draw him on a narrow screen: he
    // is then laid out nowhere. A browser says of each whether it is laid out, and says so
    // again when the window is made wider. jsdom lays nothing out, so a browser is stood in
    // for here: the page is laid out, and he is not.
    const laidOut = new Set<Element>([document.documentElement]);
    jest.spyOn(Element.prototype, "getClientRects").mockImplementation(function rects(this: Element) {
      return (laidOut.has(this) ? [{}] : []) as unknown as DOMRectList;
    });
    const watchers: (() => void)[] = [];
    class Watcher {
      constructor(private readonly tell: () => void) {}
      observe() {
        watchers.push(this.tell);
      }
      disconnect() {
        watchers.splice(watchers.indexOf(this.tell), 1);
      }
    }
    Object.defineProperty(globalThis, "ResizeObserver", { value: Watcher, configurable: true, writable: true });

    const { unmount } = render(<Page draws="hops" />);
    // He is held by the page and drawn nowhere on it: so the board and the foot draw him.
    expect([his("header"), his("main"), his("footer")]).toEqual([["sits"], ["hops"], ["sits"]]);

    // The window is made wider, and the page draws him: the board and the foot let him go.
    const onThePage = document.querySelector("main [data-pose] > [aria-hidden]") as Element;
    laidOut.add(onThePage);
    act(() => watchers.forEach((tell) => tell()));
    expect([his("header"), his("main"), his("footer")]).toEqual([[], ["hops"], []]);

    // And narrower again.
    laidOut.delete(onThePage);
    act(() => watchers.forEach((tell) => tell()));
    expect([his("header"), his("main"), his("footer")]).toEqual([["sits"], ["hops"], ["sits"]]);

    // Nothing is left watching once the page is gone.
    unmount();
    expect(watchers).toEqual([]);
  });

  test("test_nothing_of_it_is_kept_by_the_browser", () => {
    const { unmount } = render(<Page draws="sits" />);
    unmount();

    expect([window.localStorage.length, window.sessionStorage.length, document.cookie]).toEqual([0, 0, ""]);
  });
});
