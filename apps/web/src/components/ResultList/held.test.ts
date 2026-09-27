import { bringBeside, hold, pressedIn, putBack } from "./held";

/**
 * jsdom lays nothing out, so a test says where a part stands in the window, and where the
 * page stands. What is held here is what is done with the two: the figures are those a
 * browser gave, at 390 by 844, of the first result of a plain search.
 */
const page = { at: 0 };
const moves: { by?: number; to?: number; how?: string }[] = [];

function stands(part: Element, at: () => number): void {
  jest.spyOn(part, "getBoundingClientRect").mockImplementation(() => ({ top: at(), bottom: at() + 34 }) as DOMRect);
}

const frame = () => new Promise<void>((done) => requestAnimationFrame(() => done()));

beforeEach(() => {
  page.at = 460;
  moves.length = 0;
  document.body.innerHTML = `
    <main>
      <div id="map"><button id="pin">Rank 3</button></div>
      <ol id="list">
        <li data-area="one">
          <h3><a id="name" href="/synthetic/one">One</a></h3>
          <span data-chosen="false"><button id="compare">Add to compare</button></span>
          <button id="line" aria-expanded="false"><span id="words">Leafy</span></button>
          <button id="working" aria-expanded="false">Show the working</button>
          <button id="on-map">Show One on the map</button>
        </li>
        <li data-area="three" id="third"></li>
      </ol>
      <button id="refine" aria-expanded="false">Refine search</button>
    </main>`;
  Object.defineProperty(window, "scrollY", { configurable: true, get: () => page.at });
  Object.defineProperty(window, "scrollBy", {
    configurable: true,
    value: ({ top, behavior }: ScrollToOptions) => {
      page.at += top ?? 0;
      moves.push({ by: top, how: behavior });
    },
  });
  Object.defineProperty(window, "scrollTo", {
    configurable: true,
    value: ({ top, behavior }: ScrollToOptions) => {
      page.at = top ?? 0;
      moves.push({ to: top, how: behavior });
    },
  });
});

afterEach(() => {
  for (const name of ["scrollY", "scrollBy", "scrollTo"]) delete (window as unknown as Record<string, unknown>)[name];
  delete (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView;
});

const the = (id: string) => document.getElementById(id) as HTMLElement;

describe("what is pressed in a result stays under the hand", () => {
  test("test_a_press_that_opens_in_place_is_held_and_a_press_that_leads_elsewhere_is_not", () => {
    const list = the("list");

    // Each says whether what it opens is open, or whether its area is chosen.
    expect(pressedIn(list, the("working"))).toBe(the("working"));
    expect(pressedIn(list, the("compare"))).toBe(the("compare"));
    // A press lands on what is drawn on a button, and is a press on the button.
    expect(pressedIn(list, the("words"))).toBe(the("line"));
    // The name leads to the page of the area, and "Show on the map" to the map: the page goes where they lead.
    expect(pressedIn(list, the("name"))).toBeNull();
    expect(pressedIn(list, the("on-map"))).toBeNull();
    // What opens in place outside the list is not the list's to hold.
    expect(pressedIn(list, the("refine"))).toBeNull();
    expect(pressedIn(list, null)).toBeNull();
  });

  test("test_the_page_is_put_back_by_as_much_as_what_was_pressed_went", async () => {
    // Seen in a browser, on a phone, with the page scrolled by 460: "Show the working" stood
    // at 317.5 of the window and then at -1316.5. The browser had held the page by what
    // refines the search, which is drawn under the first result, and sent it 1,634 px down.
    const working = the("working");
    stands(working, () => 317.5 - (page.at - 460));
    // What the browser does of itself as the working opens: the page goes down by as much as the working is high.
    const theBrowserThrowsThePage = () => {
      page.at += 1634;
    };

    hold(working);
    theBrowserThrowsThePage();
    expect(working.getBoundingClientRect().top).toBe(-1316.5);
    await frame();

    expect(moves).toEqual([{ by: -1634, how: "instant" }]);
    expect(page.at).toBe(460);
    expect(working.getBoundingClientRect().top).toBe(317.5);
    // It is looked at again in the frame after, and nothing more is done: it stands where it stood.
    await frame();
    expect(moves).toHaveLength(1);
  });

  test("test_what_stands_where_it_stood_moves_nothing", async () => {
    const working = the("working");
    stands(working, () => 477.5);

    hold(working);
    await frame();
    await frame();

    expect(moves).toEqual([]);
    // Nor does what a browser rounds: a third of a pixel is not seen.
    expect(putBack(working, 477.2)).toBe(0);
    expect(moves).toEqual([]);
  });

  test("test_what_went_from_the_page_with_its_press_is_not_looked_for", () => {
    const working = the("working");
    stands(working, () => 12);
    working.remove();

    expect(putBack(working, 317.5)).toBe(0);
    expect(moves).toEqual([]);
  });
});

describe("a result that is chosen elsewhere", () => {
  const brought: { area: string | null; how: ScrollIntoViewOptions }[] = [];
  /** How far the page goes to bring the third result into view. */
  const TO_THE_RESULT = 1108;

  beforeEach(() => {
    brought.length = 0;
    Element.prototype.scrollIntoView = function scrollIntoView(this: Element, how?: boolean | ScrollIntoViewOptions) {
      brought.push({ area: this.getAttribute("data-area"), how: how as ScrollIntoViewOptions });
      page.at += TO_THE_RESULT;
    };
  });

  test("test_it_is_brought_into_view_where_what_was_pressed_stays_in_the_window", () => {
    // Beside the list the map has come to rest at the head of the window, and stays there as the page scrolls.
    stands(the("pin"), () => 91);

    expect(bringBeside(the("list"), the("third"), the("pin"), true)).toBe(true);

    // The page is taken there and back at once, to see whether the pin stays, and then it glides there.
    expect(brought).toEqual([
      { area: "three", how: { block: "nearest", behavior: "instant" } },
      { area: "three", how: { block: "nearest", behavior: "smooth" } },
    ]);
    expect(moves).toEqual([{ to: 460, how: "instant" }]);
  });

  test("test_the_page_is_left_where_it_is_where_what_was_pressed_would_go_from_under_the_hand", () => {
    // On a phone the map goes with the page: the pin stood at 329.5 and went to -778.5.
    stands(the("pin"), () => 329.5 - (page.at - 460));

    expect(bringBeside(the("list"), the("third"), the("pin"), true)).toBe(false);

    expect(brought).toEqual([{ area: "three", how: { block: "nearest", behavior: "instant" } }]);
    expect(moves).toEqual([{ to: 460, how: "instant" }]);
    expect(page.at).toBe(460);
    expect(the("pin").getBoundingClientRect().top).toBe(329.5);
  });

  test("test_a_press_made_in_the_list_brings_nothing_since_the_result_is_where_the_person_is", () => {
    // "Show on the map" takes the page to the map. Brought back to the result, the map was out of sight.
    stands(the("on-map"), () => 524);

    expect(bringBeside(the("list"), document.querySelector("[data-area='one']") as Element, the("on-map"), true)).toBe(false);

    expect(brought).toEqual([]);
    expect(moves).toEqual([]);
  });

  test("test_where_nothing_is_known_of_what_was_pressed_the_page_is_left_where_it_is", () => {
    // Not every browser gives the focus to a button that is pressed.
    expect(bringBeside(the("list"), the("third"), document.body, true)).toBe(false);
    expect(bringBeside(the("list"), the("third"), null, true)).toBe(false);

    expect(brought).toEqual([]);
    expect(moves).toEqual([]);
  });

  test("test_where_less_movement_is_asked_for_the_list_jumps_and_does_not_glide", () => {
    stands(the("pin"), () => 91);

    expect(bringBeside(the("list"), the("third"), the("pin"), false)).toBe(true);

    expect(brought.at(-1)).toEqual({ area: "three", how: { block: "nearest", behavior: "auto" } });
  });
});
