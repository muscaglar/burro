import { readFileSync } from "node:fs";
import path from "node:path";

import { cleanup, render, screen, within } from "@testing-library/react";

import { TOWN } from "@/content/town";
import { TOWNS } from "@/content/towns";
import { recordedAnswer } from "@/lib/api/recorded";
import { bandsOf, marksOf, type Mark } from "@/lib/town/bands";
import { CANVAS } from "@/lib/town/pieces";
import { saidOf } from "@/lib/town/said";
import { DRAWN_FROM, PARTS, type Part } from "@/lib/town/vibes";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { ROUGH, sayingSo } from "../../../test/support/rough";
import { Town } from "./Town";

const meta = recordedAnswer("get_meta", "meta").body.data;
const { areas, bands } = recordedAnswer("list_areas", "areas").body.data;
const pageOf = (slug: string) => recordedAnswer("get_area", `area/${slug}`).body.data;

/** Marks made by hand: the band of each part that is named, and no band for the rest. */
const marksFor = (known: Partial<Record<Part, number>>): Mark[] =>
  PARTS.map((part) => {
    const band = known[part] ?? null;
    return { tag_id: DRAWN_FROM[part], band, spread_low: band, spread_high: band };
  });

/** The towns that are hard to draw: nothing known, one part known, and every part at an end. */
const HARD: readonly (readonly [string, Partial<Record<Part, number>>])[] = [
  ["nothing known", {}],
  ["trees alone", { trees: 2 }],
  ["height alone", { height: 4 }],
  ["lit windows alone", { lit: 3 }],
  ["roofs alone", { roofs: 5 }],
  ["every band at its least", { trees: 1, height: 1, lit: 1, roofs: 1 }],
  ["every band at its most", { trees: 5, height: 5, lit: 5, roofs: 5 }],
];

const drawing = () => screen.getByRole("img");
const piecesOf = (container: HTMLElement) => [...container.querySelectorAll<HTMLElement>("[role='img'] > span")];
/** What a piece is handed: its picture, its frame and where it stands. */
const handed = (piece: HTMLElement) =>
  ["--art", "--w", "--h", "--frames", "--frame", "--x", "--y"].map((name) => piece.style.getPropertyValue(name));
/**
 * What is in sight: the words of the page, without what is said to a screen reader alone.
 * A town holds its line twice, whole and in short, and a style sheet draws one of the two.
 * jsdom reads no style sheet, so what is in sight is read as it is drawn everywhere but at
 * the head of the page of an area on a narrow screen: with the whole line, and not the short one.
 */
const inSight = (container: HTMLElement) => {
  const drawn = container.cloneNode(true) as HTMLElement;
  drawn.querySelectorAll("[data-line='short']").forEach((short) => short.remove());
  return (drawn.textContent ?? "").replace(/\s+/g, " ").trim();
};

describe("the town of an area", () => {
  test.each(areas.map(({ slug, name }) => [name, slug]))(
    "test_it_never_stands_without_the_line_that_says_it_is_no_picture_of_the_place: %s",
    (name, slug) => {
      const { container } = render(<Town marks={pageOf(slug).tags} meta={meta} of={name} />);
      const line = screen.getByText(TOWN.line);

      expect(line).toBeVisible();
      // It is in sight: nothing about it keeps it for a screen reader alone, or from one.
      expect(line.closest(".visually-hidden, [hidden], [aria-hidden='true']")).toBeNull();
      expect(container.querySelector("figure")).toContainElement(line);
      expect(container.querySelector("figcaption")).toContainElement(line);
    },
  );

  test.each(HARD)("test_the_line_stands_with_a_town_that_is_hard_to_draw: %s", (_, known) => {
    render(<Town marks={marksFor(known)} meta={meta} />);

    expect(screen.getByText(TOWN.line)).toBeVisible();
  });

  test("test_the_line_says_that_it_is_drawn_from_four_of_the_areas_vibes_and_is_not_a_picture_of_the_place", () => {
    expect(TOWN.line).toBe(
      "This little town is a drawing based on four of the area's vibes. This means it shows the character of the area, and is not a picture of what the place looks like.",
    );
    // However it is worded, it says both: what a town is drawn from, and what it is not.
    expect(TOWN.line).toMatch(/\bfour of the area's vibes\b/);
    expect(TOWN.line).toMatch(/\bnot a picture of\b.*\bplace\b/);
    expect(PARTS).toHaveLength(4);
  });

  test("test_in_short_the_line_says_both_things_the_line_says_in_one_whole_sentence", () => {
    expect(TOWN.short).toBe("This little town is a drawing based on four of the area's vibes, and not a picture of the place.");
    // However it is worded, it says what a town is drawn from and what it is not, as the line does.
    expect(TOWN.short).toMatch(/\bfour of the area's vibes\b/);
    expect(TOWN.short).toMatch(/\bnot a picture of\b.*\bplace\b/);
    // It is one sentence that is joined, and no fragment: it begins with its subject and has its verb.
    expect(TOWN.short).toMatch(/^This little town is\b.*, and\b.*\.$/);
    expect(TOWN.short.split(". ")).toHaveLength(1);
    expect(TOWN.short.length).toBeLessThan(TOWN.line.length * 0.6);
    // It is said of one town as the short line of towns that stand together is said of each.
    expect(TOWN.short.replace(/^This/, "Each")).toBe(TOWNS.short);
    expect(/\d/.test(TOWN.short)).toBe(false);
  });

  test("test_a_town_holds_its_line_whole_and_in_short_and_the_short_one_stands_outside_what_it_says_under_its_drawing", () => {
    const { container } = render(<Town marks={pageOf(areas[0]?.slug ?? "").tags} meta={meta} of={areas[0]?.name ?? ""} />);
    const town = container.querySelector("figure") as HTMLElement;
    const short = screen.getByText(TOWN.short);

    // The drawing, the line in short, and what the town says under its drawing, which is
    // the last thing it holds, as what a figure says of itself must be.
    expect([...town.children].map((part) => part.tagName)).toEqual(["SPAN", "SPAN", "FIGCAPTION"]);
    expect(short.parentElement).toBe(town);
    expect(short).toHaveAttribute("data-line", "short");
    // Whatever lays a town out finds under its drawing what it found: the line first, and nothing of the short one.
    const says = town.querySelector("figcaption") as HTMLElement;
    expect(says.firstElementChild?.textContent).toBe(TOWN.line);
    expect(says.textContent).toBe(TOWN.line);
    expect(says).not.toContainElement(short);
    // Neither is kept for a screen reader alone, or from one: the one that is drawn is heard.
    expect(short.closest(".visually-hidden, [hidden], [aria-hidden='true']")).toBeNull();
    expect(container.querySelectorAll("a, button, [tabindex]")).toHaveLength(0);
  });

  test("test_the_line_in_short_is_drawn_at_the_head_of_the_page_of_an_area_on_a_narrow_screen_and_nowhere_else", () => {
    // Measured on a phone, 390 by 844: the whole line stood beside the drawing in six lines,
    // 122 px, and what the area is like began under the first screen. In short it is four lines.
    const rules = rulesOf(readFileSync(path.join(__dirname, "Town.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, ""));
    const ofTheShort = rules.filter((rule) => /\.short\b/.test(rule.selector) || /data-town/.test(rule.selector));
    const HEAD = ":global(header[data-town]) > .town";

    expect(ofTheShort.map((rule) => [rule.under, rule.selector, rule.sets.get("display")])).toEqual([
      [null, ".short", "none"],
      ["@media (max-width: 39.99rem)", `${HEAD} > .short`, "block"],
      ["@media (max-width: 39.99rem)", `${HEAD} > .says > .line`, "none"],
      ["@media (max-width: 39.99rem)", `${HEAD} > .says:not(:has(> :not(.line)))`, "none"],
    ]);
    // It is read as the line is read: in the reading face, at the size of the line.
    const drawn = new Map(ofTheShort.filter((rule) => rule.selector === `${HEAD} > .short`).flatMap((rule) => [...rule.sets]));
    const line = new Map(rules.filter((rule) => rule.selector === ".says" && rule.under === null).flatMap((rule) => [...rule.sets]));
    expect([drawn.get("font"), drawn.get("flex"), drawn.get("max-width")]).toEqual([line.get("font"), line.get("flex"), line.get("max-width")]);
    // The head of that page is known by what it says of where its town stands. If it comes
    // to say it another way, the town must be told: this fails.
    const head = readFileSync(path.join(__dirname, "../AreaProfile/AreaProfile.tsx"), "utf8");
    expect(/<Frame kind="box" as="header"[^>]*\bdata-town=\{townStands\}>/.test(head)).toBe(true);
    expect(/<\/h1>[\s\S]*<Town\b[\s\S]*<\/Frame>/.test(head)).toBe(true);
  });

  test("test_it_says_to_a_screen_reader_what_it_is_made_of_band_by_band_in_the_words_of_the_service", () => {
    for (const { slug, name } of areas) {
      const { tags } = pageOf(slug);
      const { unmount } = render(<Town marks={tags} meta={meta} of={name} />);
      const said = saidOf(tags, meta);

      expect(drawing()).toHaveAccessibleName(
        [`${TOWN.nameOf(name)}.`, ...said.map((part) => `${part.name}: ${part.says}.`)].join(" "),
      );
      // Each of the four vibes is named as the service names it, in the order the parts are said in.
      const labels = PARTS.map((part) => meta.tags.find((tag) => tag.tag_id === DRAWN_FROM[part])?.label ?? "");
      const heard = drawing().getAttribute("aria-label") ?? "";
      expect(labels.map((label) => heard.indexOf(label))).toEqual([...labels.map((label) => heard.indexOf(label))].sort((a, b) => a - b));
      expect(labels.every((label) => label !== "" && heard.includes(label))).toBe(true);
      unmount();
    }
  });

  test("test_the_name_of_the_area_is_said_and_is_not_drawn_and_a_town_with_no_name_says_none", () => {
    const [{ slug, name } = { slug: "", name: "" }] = areas;
    const named = render(<Town marks={pageOf(slug).tags} meta={meta} of={name} />);

    expect(drawing().getAttribute("aria-label")).toContain(name);
    expect(inSight(named.container)).not.toContain(name);
    named.unmount();

    render(<Town marks={pageOf(slug).tags} meta={meta} />);
    expect((drawing().getAttribute("aria-label") ?? "").startsWith(`${TOWN.name}.`)).toBe(true);
    expect(drawing().getAttribute("aria-label")).not.toContain(name);
  });

  test("test_nothing_is_in_sight_but_the_line_where_the_whole_town_is_drawn_no_rank_no_fit_and_no_figure", () => {
    const whole = areas.filter(({ slug }) => PARTS.every((part) => bandsOf(pageOf(slug).tags)[part] !== null));

    expect(whole.length).toBeGreaterThan(10);
    for (const { slug, name } of whole) {
      const { container, unmount } = render(<Town marks={pageOf(slug).tags} meta={meta} of={name} />);
      expect(inSight(container)).toBe(TOWN.line);
      expect(/\d/.test(inSight(container))).toBe(false);
      unmount();
    }
  });

  test("test_whatever_lays_it_out_may_say_where_it_stands_and_it_is_drawn_as_it_was", () => {
    const { container } = render(<Town marks={pageOf(areas[0]?.slug ?? "").tags} meta={meta} className="placed" />);
    const town = container.querySelector("figure");

    expect(town).toHaveClass("placed");
    expect(town?.classList.length).toBe(2);
  });

  test("test_it_can_be_neither_pressed_nor_given_the_focus", () => {
    const { container } = render(<Town marks={pageOf(areas[0]?.slug ?? "").tags} meta={meta} written />);

    expect(container.querySelectorAll("a, button, input, select, textarea, summary, [tabindex], [role='button']")).toHaveLength(0);
  });
});

describe("what is drawn of a town", () => {
  test("test_it_is_of_one_size_for_every_area_the_first_result_as_the_tenth", () => {
    const sizes = recordedAnswer("rank", "rank-first").body.data.ranked.map(({ area_id }) => {
      const { unmount } = render(<Town marks={marksOf(bands, area_id)} meta={meta} />);
      const size = [
        drawing().style.getPropertyValue("--across"),
        drawing().style.getPropertyValue("--down"),
        drawing().getAttribute("data-size"),
      ];
      unmount();
      return size.join(" ");
    });

    expect(sizes.length).toBeGreaterThanOrEqual(10);
    expect(new Set(sizes)).toEqual(new Set([`${CANVAS.width} ${CANVAS.height} small`]));
  });

  test("test_two_areas_with_the_same_four_bands_are_drawn_the_same_whatever_they_are_called", () => {
    const one = render(<Town marks={marksFor({ trees: 2, height: 4, lit: 3, roofs: 1 })} meta={meta} of="One name" />);
    const first = piecesOf(one.container).map(handed);
    one.unmount();
    // Every other vibe of the second area differs, and so does its name.
    const others: Mark[] = meta.tags.map((tag) => ({ tag_id: tag.tag_id, band: 5, spread_low: 5, spread_high: 5 }));
    const other = render(
      <Town marks={[...marksFor({ trees: 2, height: 4, lit: 3, roofs: 1 }), ...others]} meta={meta} of="Another name" />,
    );

    expect(first.length).toBeGreaterThan(5);
    expect(piecesOf(other.container).map(handed)).toEqual(first);
  });

  test("test_a_result_and_the_page_of_its_area_draw_one_town", () => {
    for (const { area_id, slug } of areas) {
      const result = render(<Town marks={marksOf(bands, area_id)} meta={meta} />);
      const onResult = piecesOf(result.container).map(handed);
      result.unmount();
      const page = render(<Town marks={pageOf(slug).tags} meta={meta} large written />);

      expect([slug, piecesOf(page.container).map(handed)]).toEqual([slug, onResult]);
      page.unmount();
    }
  });

  test("test_every_piece_is_a_drawing_of_a_town_served_from_the_websites_own_origin_at_its_own_size", () => {
    const { container } = render(<Town marks={marksFor({ trees: 5, height: 3, lit: 4, roofs: 2 })} meta={meta} />);
    const pieces = piecesOf(container);

    expect(pieces.length).toBeGreaterThan(10);
    for (const piece of pieces) {
      expect(piece.style.getPropertyValue("--art")).toMatch(/^url\("\/art\/town-[a-z]+\.png"\)$/);
      for (const length of ["--w", "--h", "--frames", "--frame", "--x", "--y"]) {
        expect([length, /^\d+$/.test(piece.style.getPropertyValue(length))]).toEqual([length, true]);
      }
    }
  });

  test("test_it_is_drawn_larger_only_where_it_is_told_that_it_stands_beside_a_title", () => {
    const small = render(<Town marks={marksFor({ height: 2 })} meta={meta} />);
    expect(drawing()).toHaveAttribute("data-size", "small");
    small.unmount();

    render(<Town marks={marksFor({ height: 2 })} meta={meta} large />);
    expect(drawing()).toHaveAttribute("data-size", "large");
  });
});

describe("what a town leaves blank", () => {
  test("test_what_is_not_drawn_is_said_in_sight_under_the_line_part_by_part", () => {
    const { container } = render(<Town marks={marksFor({ height: 3, lit: 2 })} meta={meta} />);
    const said = `${TOWN.leftBlank([TOWN.listed.trees, TOWN.listed.roofs])} ${TOWN.whyBlank.unknown}`;

    expect(screen.getByText(said)).toBeVisible();
    expect(inSight(container)).toBe(`${TOWN.line}${said}`);
  });

  test("test_the_recorded_areas_that_cannot_be_placed_say_in_sight_which_part_is_blank_and_why_to_a_screen_reader", () => {
    const partly = areas.filter(({ slug }) => PARTS.some((part) => bandsOf(pageOf(slug).tags)[part] === null));

    expect(partly.length).toBeGreaterThan(2);
    for (const { slug, name } of partly) {
      const { tags } = pageOf(slug);
      const { unmount } = render(<Town marks={tags} meta={meta} of={name} />);
      const blank = saidOf(tags, meta).filter(({ state }) => state !== "drawn");

      expect(screen.getByText(`${TOWN.leftBlank(blank.map(({ part }) => TOWN.listed[part]))} ${TOWN.whyBlank.unknown}`)).toBeVisible();
      for (const { says } of blank) expect(drawing().getAttribute("aria-label")).toContain(says);
      unmount();
    }
  });

  test("test_a_release_that_lacks_a_vibe_draws_nothing_of_it_and_says_so", () => {
    const without = { ...meta, tags: meta.tags.filter((tag) => tag.tag_id !== DRAWN_FROM.trees) };
    const held = render(<Town marks={marksFor({ trees: 4, height: 3, lit: 3, roofs: 3 })} meta={meta} />);
    const trees = (container: HTMLElement) => piecesOf(container).filter((piece) => /town-trees/.test(piece.style.getPropertyValue("--art")));
    expect(trees(held.container)).toHaveLength(4);
    held.unmount();

    const { container } = render(<Town marks={marksFor({ trees: 4, height: 3, lit: 3, roofs: 3 })} meta={without} />);

    // The ring that marks where a tree would stand, and no tree.
    expect(trees(container).map((piece) => piece.style.getPropertyValue("--frame"))).toEqual(["0"]);
    expect(screen.getByText(`${TOWN.leftBlank([TOWN.listed.trees])} ${TOWN.whyBlank.unknown}`)).toBeVisible();
    expect(drawing().getAttribute("aria-label")).toContain(TOWN.because(TOWN.blank.trees, TOWN.notHeld));
  });
});

describe("what the rules of the website ask of a town", () => {
  const changed = (part: Part, change: (tag: (typeof meta.tags)[number]) => (typeof meta.tags)[number]) => ({
    ...meta,
    tags: meta.tags.map((tag) => (tag.tag_id === DRAWN_FROM[part] ? change(tag) : tag)),
  });

  test("test_a_vibe_that_counts_recorded_crime_is_left_blank_and_says_why_since_nobody_asked_for_a_town", () => {
    const crime = meta.features.find((one) => one.dimension === "crime");
    if (crime === undefined) throw new Error("The recorded release holds no measure of recorded crime.");
    const release = changed("lit", (tag) => ({
      ...tag,
      terms: [...tag.terms, { feature_id: crime.feature_id, hundredths: 10, reading: "high" }],
    }));
    const { container } = render(<Town marks={marksFor({ trees: 3, height: 3, lit: 5, roofs: 3 })} meta={release} />);
    const label = meta.tags.find((tag) => tag.tag_id === DRAWN_FROM.lit)?.label ?? "";

    // Every window is dark, and none is lit: the first frame of each wall.
    const walls = piecesOf(container).filter((piece) => /town-(low|mid|tall)/.test(piece.style.getPropertyValue("--art")));
    expect(walls.map((wall) => wall.style.getPropertyValue("--frame"))).toEqual(["0", "0", "0", "0"]);
    // In sight it says which part is blank, and that it is for recorded crime and not for want of a figure.
    expect(screen.getByText(`${TOWN.leftBlank([TOWN.listed.lit])} ${TOWN.whyBlank.crime}`)).toBeVisible();
    expect(drawing().getAttribute("aria-label")).toContain(TOWN.because(TOWN.blank.lit, TOWN.countsCrime(label)));
  });

  test("test_a_vibe_the_service_says_is_less_sure_is_drawn_as_every_vibe_is_and_the_town_says_nothing_of_it", () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a user".
    // No service calls a vibe a town is drawn from less sure. Here one does, and says so of
    // it in the words a service gave such a vibe until it stopped: its label, and why.
    const release = sayingSo(meta, [DRAWN_FROM.roofs]);
    const marks = marksFor({ trees: 3, height: 3, lit: 3, roofs: 4 });
    const { container } = render(<Town marks={marks} meta={release} />);
    const drawn = piecesOf(container).map((piece) => [piece.style.getPropertyValue("--art"), piece.style.getPropertyValue("--frame")]);

    expect(release.tags.find((tag) => tag.tag_id === DRAWN_FROM.roofs)?.sureness).toBe("rough_guide");
    expect(release.rough_guides).toContainEqual({ ...ROUGH, tag_id: DRAWN_FROM.roofs });
    expect(screen.queryByRole("note")).toBeNull();
    expect(container.querySelector("[data-rough-guide]")).toBeNull();
    expect([container.textContent?.includes(ROUGH.label), container.textContent?.includes(ROUGH.why)]).toEqual([false, false]);
    expect([drawing().getAttribute("aria-label")?.includes(ROUGH.label), drawing().getAttribute("aria-label")?.includes(ROUGH.why)]).toEqual([false, false]);
    // Under its drawing the town says its line, and nothing else where the whole of it is drawn.
    expect([...(screen.getByText(TOWN.line).closest("figcaption")?.children ?? [])].map((one) => one.textContent)).toEqual([TOWN.line]);
    // And it is the town that is drawn of a release that says nothing of how sure a vibe is.
    cleanup();
    const plain = render(<Town marks={marks} meta={meta} />);
    expect(piecesOf(plain.container).map((piece) => [piece.style.getPropertyValue("--art"), piece.style.getPropertyValue("--frame")])).toEqual(drawn);
  });
});

describe("a town with its parts written out", () => {
  test("test_each_part_is_written_under_the_line_with_what_it_is_drawn_from_and_is_not_said_twice", () => {
    const { tags } = pageOf(areas[0]?.slug ?? "");
    render(<Town marks={tags} meta={meta} of={areas[0]?.name ?? ""} written />);
    const parts = screen.getByRole("list", { hidden: false, name: TOWN.madeOf });
    const said = saidOf(tags, meta);

    expect(screen.getByText(TOWN.line)).toBeVisible();
    expect(within(parts).getAllByRole("listitem").map((part) => [...part.children].map((child) => child.textContent))).toEqual(
      said.map(({ name, says }) => [name, says]),
    );
    // The drawing says what it is, and leaves its parts to the words under it.
    expect(drawing()).toHaveAccessibleName(`${TOWN.nameOf(areas[0]?.name ?? "")}.`);
  });

  test("test_a_part_that_is_blank_says_so_among_the_parts_and_the_short_line_gives_way", () => {
    render(<Town marks={marksFor({ trees: 3, height: 3 })} meta={meta} written />);
    const label = (part: Part) => meta.tags.find((tag) => tag.tag_id === DRAWN_FROM[part])?.label ?? "";

    expect(screen.getByText(TOWN.because(TOWN.blank.lit, TOWN.notKnown(label("lit"))))).toBeVisible();
    expect(screen.getByText(TOWN.because(TOWN.blank.roofs, TOWN.notKnown(label("roofs"))))).toBeVisible();
    expect(screen.queryByText(TOWN.leftBlank([TOWN.listed.lit, TOWN.listed.roofs]), { exact: false })).toBeNull();
  });
});

describe("a town on the grass", () => {
  test("test_it_says_where_it_stands_so_that_its_words_are_given_a_box_to_be_read_in", () => {
    const onGrass = render(<Town marks={marksFor({ height: 2 })} meta={meta} onGrass />);
    expect(onGrass.container.querySelector("figure")).toHaveAttribute("data-on", "grass");
    onGrass.unmount();

    const { container } = render(<Town marks={marksFor({ height: 2 })} meta={meta} />);
    expect(container.querySelector("figure")).toHaveAttribute("data-on", "page");
  });
});

describe("the accessibility of a town", () => {
  test.each([
    ["as it stands on a result", {}],
    ["with its parts written out", { written: true }],
    ["on the grass", { onGrass: true }],
    ["beside a title", { large: true, written: true }],
  ])("test_it_has_no_accessibility_fault: %s", async (_, how) => {
    const { container } = render(
      <div>
        <Town marks={pageOf(areas[0]?.slug ?? "").tags} meta={meta} of={areas[0]?.name ?? ""} {...how} />
        <Town marks={marksFor({ trees: 1 })} meta={meta} {...how} />
        <Town marks={[]} meta={{ tags: [], features: [] }} {...how} />
      </div>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
