/**
 * What the page of an area holds before anything is opened. docs/design/web.md,
 * section 4.2.
 *
 * The page is at most four screens of a desktop and seven of a phone before
 * anything is opened. jsdom lays nothing out, so no test measures a height.
 * This holds what the measured heights depend on: what is drawn at first, and
 * what is closed. A change that draws more at first fails here, and is to be
 * measured in a browser before a count is raised.
 */

import { render, screen } from "@testing-library/react";

import AreaPage from "@/app/[city]/[area]/page";
import { Shell } from "@/components/Shell/Shell";
import { LOOK, PORTRAIT } from "@/content/area";
import { TRAY } from "@/content/compare";
import { recordedAnswer } from "@/lib/api/recorded";

jest.mock("next/navigation", () => ({
  ...jest.requireActual("next/navigation"),
  usePathname: () => "/synthetic/alderwick",
}));

const meta = recordedAnswer("get_meta", "meta").body;
const SLUGS = recordedAnswer("list_areas", "areas").body.data.areas.map((area) => area.slug);

/**
 * What was measured in a browser on 2026-09-23, with a little room: section 4.2. The portrait
 * opens with what the area is like in short and where it is, and says once what it cannot
 * place. The most any page of the made-up release drew then was 151 lines and 32 controls.
 * A release carried twelve vibes for a time, which was one line more on a page that places
 * them all: the most was 161, and the room was used up. It carries eleven again. The census
 * of an area is a part of the page that is closed at first. It draws two lines, and one in
 * the list of contents, so the most was 164 with twelve vibes. Neither was measured again.
 */
const AT_FIRST = { lines: 164, controls: 36, vibes: 14, stations: 4 } as const;
/** The parts that are closed until they are pressed, by the id the list of contents names them by. */
const CLOSED = ["alike", "cost", "measured", "sources", "census"] as const;

async function show(slug: string) {
  render(<Shell meta={meta.meta}>{await AreaPage({ params: Promise.resolve({ city: "synthetic", area: slug }) })}</Shell>);
  return screen.getByRole("main");
}

/** True for what is drawn while every part that opens is closed: what no such part holds, and what opens one. */
function drawnAtFirst(element: Element): boolean {
  const held = element.closest("details");
  if (held === null) return true;
  const opens = element.closest("summary");
  return opens !== null && opens.parentElement === held && held.parentElement?.closest("details") === null;
}

describe.each(SLUGS)("the page of %s, before anything is opened", (slug) => {
  test("test_nothing_is_open", async () => {
    const main = await show(slug);

    expect([...main.querySelectorAll("details")].filter((part) => part.open)).toEqual([]);
    expect(main.querySelectorAll("[aria-expanded='true']")).toHaveLength(0);
  });

  test("test_what_is_long_is_closed_and_the_portrait_is_not", async () => {
    const main = await show(slug);

    for (const id of CLOSED) expect(main.querySelector(`details#${id}`)).not.toBeNull();
    // Cost, every figure and every source are one press away, and none is drawn at first.
    const rows = [...main.querySelectorAll("[role='group'][aria-label]")].filter(drawnAtFirst);
    const stations = rows.filter((row) => /station/i.test(row.getAttribute("aria-label") ?? ""));
    expect(rows.length - stations.length).toBe(1);
    expect(stations.length).toBeLessThanOrEqual(AT_FIRST.stations);
    expect(main.querySelector("section[aria-labelledby='character']")?.closest("details")).toBeNull();
  });

  test("test_the_page_opens_with_the_portrait_and_ends_with_go_and_look", async () => {
    const main = await show(slug);

    const parts = [...main.querySelectorAll("article h2")]
      .filter(drawnAtFirst)
      .map((heading) => heading.textContent)
      .filter((title) => title !== TRAY.title);

    expect(parts[0]).toBe(PORTRAIT.title);
    expect(parts.at(-1)).toBe(LOOK.title);
  });

  test("test_each_vibe_is_one_line_and_no_more_is_drawn_than_was_measured", async () => {
    const main = await show(slug);

    const vibes = main.querySelectorAll("section[aria-labelledby='character'] details[data-vibe]");
    const opened = main.querySelectorAll("section[aria-labelledby='character'] > [role='group'] details:not([data-vibe])");
    const lines = [...main.querySelectorAll("h1, h2, h3, h4, p, li, summary, dt, dd")].filter(drawnAtFirst);
    const controls = [...main.querySelectorAll("a[href], button, summary")].filter(drawnAtFirst);
    const unplaced = recordedAnswer("get_area", `area/${slug}`).body.data.portrait.unplaced.length;

    // One line for each vibe the area is placed on. What it cannot be placed on is said once,
    // with one thing to press, however many vibes that is.
    expect(vibes).toHaveLength(meta.data.tags.length - unplaced);
    expect(opened).toHaveLength(unplaced > 0 ? 1 : 0);
    expect(vibes.length).toBeLessThanOrEqual(AT_FIRST.vibes);
    // What the area is like, in short, is five lines at most.
    const short = main.querySelector("[aria-labelledby='character-short']");
    expect(short).not.toBeNull();
    expect(short?.querySelectorAll("li").length).toBeLessThanOrEqual(5);
    // One line for each vibe: its name, its mark, its band, one figure at most, and what it opens.
    for (const vibe of vibes) {
      const line = vibe.querySelector(":scope > summary");
      expect(line?.querySelectorAll("p, li, dl, table")).toHaveLength(0);
      expect(line?.querySelectorAll("[data-on]").length).toBeLessThanOrEqual(5);
    }
    expect(lines.length).toBeLessThanOrEqual(AT_FIRST.lines);
    expect(controls.length).toBeLessThanOrEqual(AT_FIRST.controls);
  });
});
