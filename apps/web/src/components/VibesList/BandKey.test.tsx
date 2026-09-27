import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { ABOUT } from "@/content/about";
import { BAND_ON_A_SCALE, BAND_ONE_WAY, BAND_VARIES } from "@/content/bands";
import { CANNOT_PLACE } from "@/content/facts";
import { KNOWN, PEG } from "@/content/kit";
import { STRIP } from "@/content/search";
import { VIBES } from "@/content/vibes";
import { recordedAnswer } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { pictureOf } from "../kit/drawings";
import { NO_PICTURE, picturesAtEnds } from "../kit/Ends/picture";
import { drawingOf } from "../kit/Thing/drawn";
import { BandKey } from "./BandKey";
import { PAIRS_MAY_STAND, PAIRS_STAND } from "./look";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
/** The first scale of the release, whichever it is: the key shows a scale by it. */
const scale = meta.tags.find((tag) => tag.low_end !== null && tag.high_end !== null);
/** The first vibe of the release that runs one way, whichever it is: the key shows the five bands by it. */
const oneWay = meta.tags.find((tag) => tag.low_end === null || tag.high_end === null);
const SHEET = rulesOf(readFileSync(path.join(__dirname, "BandKey.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, ""));
const BANDS = [1, 2, 3, 4, 5] as const;
const served = (name: Parameters<typeof pictureOf>[0]) => `url("${pictureOf(name)}")`;
/** The pictures at the two ends of a gauge of the key, the low end first, by where each is served from. */
const endsOf = (gauge: Element | null) =>
  [...(gauge?.querySelectorAll<HTMLElement>("[data-at] > [style*='/art/']") ?? [])].map((one) => one.style.getPropertyValue("--art"));

const key = () => screen.getByRole("region", { name: ABOUT.band.title });
/** The state of the key that a line of it says, by the line. */
const stateOf = (line: string) => within(key()).getByText(line).closest("li") as HTMLElement;

describe("where an area sits on a vibe, in the key", () => {
  test("test_it_is_a_part_of_the_key_under_a_heading_that_says_where_the_steps_are_met", () => {
    render(<BandKey meta={meta} />);

    expect(within(key()).getByRole("heading", { level: 3, name: ABOUT.band.title })).toHaveAttribute("id", "key-steps");
    expect(key()).toHaveTextContent(ABOUT.band.lead);
    // What is said first is said over the rows, and is no row of them.
    expect(within(key()).getByText(ABOUT.band.lead).closest("[data-key]")).toBeNull();
    // It stands in the box of the key, and is no box itself.
    expect(key()).not.toHaveAttribute("data-kind");
    expect(key().querySelector("[data-kind]")).toBeNull();
  });

  test.each(PAIRS_MAY_STAND)("test_every_state_a_band_is_drawn_in_stands_beside_the_line_that_says_what_is_seen: %s", (pairs) => {
    render(<BandKey meta={meta} pairs={pairs} />);

    const rows = [...key().querySelectorAll<HTMLElement>("[data-key]")];

    expect(rows.map((one) => [one.dataset.key, one.querySelector("[data-says] > p")?.textContent])).toEqual([
      ["one-way", ABOUT.band.states.oneWay],
      ["scale", ABOUT.band.states.scale],
      // The two pictures of every vibe, where the key has them as well as the vibes.
      ...(pairs === "key" ? [["ends", ABOUT.band.states.ends]] : []),
      ["part", ABOUT.band.states.part],
      ["mixed", ABOUT.band.states.mixed],
      ["unplaced", ABOUT.band.states.unplaced],
    ]);
    // A gauge is as wide as five steps and two pictures, and stands over its sentence on a
    // narrow screen. The two pictures of every vibe are many, and stand under theirs.
    expect(rows.map((one) => one.dataset.drawn)).toEqual(rows.map((one) => (one.dataset.key === "ends" ? "many" : "wide")));
  });

  test("test_the_two_pictures_of_every_vibe_stand_with_the_vibe_and_the_key_says_what_the_two_mean_and_where_they_are", () => {
    // The founder asked for far less in sight on this page. Every vibe of it has its gauge
    // under its map, with its two pictures: with all of them drawn in the key a second time
    // the page was 889 px higher on a phone.
    expect(PAIRS_STAND).toBe("vibe");
    render(<BandKey meta={meta} />);

    expect(key().querySelector("[data-key='ends']")).toBeNull();
    expect(within(key()).queryByRole("list", { name: ABOUT.band.pairs })).toBeNull();
    // What the two mean is said over the rows, after what a gauge is, with where the pictures of each vibe are.
    const lead = [...(within(key()).getByText(ABOUT.band.lead).parentElement?.querySelectorAll("p") ?? [])].map((one) => one.textContent);
    expect(lead).toEqual([ABOUT.band.lead, ABOUT.band.pictures]);
    expect(ABOUT.band.pictures).toMatch(/with each vibe further down this page/);
    expect(ABOUT.band.pictures).toMatch(/neither end of a gauge is the better one/);
    // The gauges of the key have the pictures of their own vibes at their ends all the same.
    expect(key().querySelectorAll("[role='img'] [data-at] > [style*='/art/']").length).toBe((BANDS.length + 4) * 2);
  });

  test("test_asked_to_the_key_has_the_two_pictures_of_every_vibe_and_says_what_the_two_mean_beside_them", () => {
    render(<BandKey meta={meta} pairs="key" />);

    // It is said once: beside the pictures, and not over the rows as well.
    expect(key().textContent?.includes(ABOUT.band.pictures)).toBe(false);
    expect(within(key()).getByRole("list", { name: ABOUT.band.pairs })).toBeInTheDocument();
  });

  test("test_the_five_bands_are_each_drawn_and_said_in_the_words_every_band_is_said_in", () => {
    render(<BandKey meta={meta} />);

    const five = within(stateOf(ABOUT.band.states.oneWay)).getByRole("list", { name: ABOUT.band.five });
    const drawn = within(five).getAllByRole("img");

    expect(drawn.map((one) => one.getAttribute("aria-label"))).toEqual(
      BANDS.map((band) => `band ${band} of 5, from least to most`),
    );
    expect(within(five).getAllByRole("listitem").map((item) => item.textContent)).toEqual(BANDS.map((band) => BAND_ONE_WAY[band]));
  });

  test("test_every_gauge_of_the_key_has_the_one_picture_of_each_end_of_its_vibe_as_a_gauge_has_wherever_it_is_met", () => {
    render(<BandKey meta={meta} />);
    if (scale === undefined || oneWay === undefined) throw new Error("The recorded release holds vibes of one kind.");

    const gauges = [...key().querySelectorAll<HTMLElement>("[role='img']")];
    // The five bands, a scale, a band that is not whole, a mixed area and one Burro could not work out.
    expect(gauges).toHaveLength(BANDS.length + 4);
    for (const gauge of gauges) {
      const shown = gauge.closest("[data-key]")?.getAttribute("data-key") === "scale" ? scale : oneWay;
      // The picture of its low end, its five steps, and the picture of its high end.
      expect([...gauge.children].map((one) => one.getAttribute("data-at") ?? "steps")).toEqual(["low", "steps", "high"]);
      expect(endsOf(gauge)).toEqual(picturesAtEnds(shown.tag_id).map(served));
      // The pictures are dress: the name of the gauge says what it shows.
      for (const picture of gauge.querySelectorAll("[data-at] > [style*='/art/']")) expect(picture).toHaveAttribute("aria-hidden", "true");
    }
    // The vibe a gauge is of is named as the service names it, with its small drawing: none is written into the website.
    for (const [shown, row] of [
      [oneWay, "one-way"],
      [scale, "scale"],
    ] as const) {
      const named = key().querySelector(`[data-key='${row}'] [data-vibe='${shown.tag_id}']`);
      expect(named?.textContent).toBe(shown.label);
      expect(named?.querySelector<HTMLElement>("[style*='/art/']")?.style.getPropertyValue("--art")).toBe(
        served(drawingOf({ kind: "tag", id: shown.tag_id, family: shown.family })),
      );
    }
  });

  test("test_a_scale_is_shown_by_a_scale_of_the_release_with_the_names_and_the_pictures_of_its_ends", () => {
    render(<BandKey meta={meta} />);
    if (scale === undefined) throw new Error("The recorded release holds no scale.");
    const [low, high] = [scale.low_end ?? "", scale.high_end ?? ""];
    const state = stateOf(ABOUT.band.states.scale);

    // The vibe is named as the service names it, and so are its ends: none is written into the website.
    expect(state).toHaveTextContent(scale.label);
    expect(within(state).getByRole("img")).toHaveAccessibleName(`band 2 of 5, from ${low} to ${high}`);
    expect(state).toHaveTextContent(BAND_ON_A_SCALE[2](low, high));
    // Each end has its picture, chosen by the id of the vibe, and its name under it.
    const gauge = within(state).getByRole("img");
    expect(endsOf(gauge)).toEqual(picturesAtEnds(scale.tag_id).map(served));
    expect([...gauge.querySelectorAll("[data-at]")].map((end) => end.textContent)).toEqual([low, high]);
  });

  test("test_asked_to_the_two_pictures_of_every_vibe_stand_in_the_key_beside_the_name_of_the_vibe", () => {
    render(<BandKey meta={meta} pairs="key" />);
    const row = stateOf(ABOUT.band.states.ends);
    const pairs = within(row).getByRole("list", { name: ABOUT.band.pairs });
    const items = within(pairs).getAllByRole("listitem");

    expect(items).toHaveLength(meta.tags.length);
    meta.tags.forEach((tag, at) => {
      const item = items[at] as HTMLElement;
      const [low, high] = [tag.low_end ?? STRIP.least, tag.high_end ?? STRIP.most];
      // The name of the vibe, and then its two ends, each under its picture: the low end first.
      expect([tag.tag_id, item.textContent]).toEqual([tag.tag_id, `${tag.label}: ${low} ${ABOUT.band.to} ${high}`]);
      expect([tag.tag_id, endsOf(item)]).toEqual([tag.tag_id, picturesAtEnds(tag.tag_id).map(served)]);
      // The two are opposites, and every vibe of the release has a pair of its own.
      const [first, last] = picturesAtEnds(tag.tag_id);
      expect([tag.tag_id, first === last, first === NO_PICTURE]).toEqual([tag.tag_id, false, false]);
      for (const picture of item.querySelectorAll("[style*='/art/']")) expect(picture.closest("[aria-hidden='true']")).not.toBeNull();
    });
    // It says that neither end of a gauge is the better one, and gives no verdict of either.
    expect(ABOUT.band.states.ends).toMatch(/neither end of a gauge is the better one/);
  });

  test("test_in_a_window_with_no_room_for_them_the_pictures_of_a_gauge_are_not_drawn_and_its_steps_are_narrower", () => {
    // Measured in a browser with the text of a phone twice as large, which is a window 195
    // wide: a scale with a picture at each end was 244 wide, and the page was 75 wider than
    // its window. A gauge says how wide it may be, and is drawn with the steps it has the
    // room of: where it has the room of no picture its ends are named, and their pictures go.
    const of = (selector: string, under: string | null = null) =>
      new Map(SHEET.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));

    expect(of(".sits").get("container-type")).toBe("inline-size");
    // Seen in a browser: a gauge that was as wide as what it held, and asked how wide it
    // was, was of no width at all, and its words stood a letter to a line. It is as wide as
    // the room it is given, and so is everything that holds it.
    expect([of(".sits").get("display"), of(".sits").get("flex"), of(".drawn").get("flex")]).toEqual(["flex", "1 1 100%", "1 1 100%"]);
    // Nothing that holds a gauge is laid at the start of its room, which would make it as wide as what it holds.
    const held = SHEET.filter((rule) => /^\.(drawn|five|sits)$/.test(rule.selector));
    expect(held.flatMap((rule) => [...rule.sets.keys()]).filter((property) => /^(justify-items|justify-self|width|float)$/.test(property))).toEqual([]);
    expect([...of(".gauge", "@container (max-width: 175px)")]).toEqual([["--track-step", "7"]]);
    expect([...of(".gauge", "@container (max-width: 155px)")]).toEqual([["--track-step", "5"]]);
    expect([...of(".end > :not(.endName)", "@container (max-width: 135px)")]).toEqual([["display", "none"]]);
    // Nothing is drawn smaller, turned or cut.
    expect(SHEET.filter((rule) => [...rule.sets.keys()].some((property) => /^(zoom|scale|transform|overflow)/.test(property)))).toEqual([]);
  });

  test("test_a_release_with_no_scale_shows_none_and_says_nothing_of_one", () => {
    const without = { ...meta, tags: meta.tags.filter((tag) => tag.low_end === null || tag.high_end === null) };
    render(<BandKey meta={without} />);

    expect(within(key()).queryByText(ABOUT.band.states.scale)).toBeNull();
    expect(within(key()).getByText(ABOUT.band.states.oneWay)).toBeInTheDocument();
    expect(key().querySelector("[data-key='scale']")).toBeNull();
  });

  test("test_a_release_of_scales_alone_shows_the_states_of_a_band_by_a_scale", () => {
    const without = { ...meta, tags: meta.tags.filter((tag) => tag.low_end !== null && tag.high_end !== null) };
    render(<BandKey meta={without} />);

    expect(key().querySelector("[data-key='one-way']")).toBeNull();
    for (const state of ["part", "mixed", "unplaced"]) {
      expect([state, endsOf(key().querySelector(`[data-key='${state}'] [role='img']`))]).toEqual([
        state,
        picturesAtEnds(without.tags[0]?.tag_id).map(served),
      ]);
    }
  });

  test("test_a_release_with_no_vibe_draws_no_gauge_and_says_what_each_state_means_all_the_same", () => {
    render(<BandKey meta={{ ...meta, tags: [] }} />);

    expect(within(key()).queryAllByRole("img")).toEqual([]);
    expect(key()).toHaveTextContent(ABOUT.band.lead);
  });

  test("test_a_band_that_is_not_whole_a_mixed_area_and_one_that_cannot_be_placed_are_each_drawn_as_they_are_wherever_they_are_met", () => {
    render(<BandKey meta={meta} />);

    // The step the peg stands on is chequered, and after the gauge stand the mark of what
    // is not whole and its two words, as they stand on a result.
    const part = stateOf(ABOUT.band.states.part);
    expect(part.querySelector("[data-part='true']")).not.toBeNull();
    const said = part.querySelector<HTMLElement>("[data-known='some']");
    expect(said?.textContent).toBe(KNOWN.some);
    expect(said?.querySelector<HTMLElement>("[style*='/art/']")?.style.getPropertyValue("--art")).toBe(served("ui-approx"));
    expect(ABOUT.band.states.part).toContain(`"${KNOWN.some}"`);
    // No other state of the key says it.
    expect(key().querySelectorAll("[data-known='some']")).toHaveLength(1);

    const mixed = stateOf(ABOUT.band.states.mixed);
    expect(mixed.querySelector("[data-range='true']")).not.toBeNull();
    expect(mixed).toHaveTextContent(BAND_VARIES);
    expect(within(mixed).getByRole("img")).toHaveAccessibleName(/^varies within this area, between band 2 and band 4 of 5/);

    const unplaced = stateOf(ABOUT.band.states.unplaced);
    expect(unplaced.querySelector("[data-placed='false']")).not.toBeNull();
    expect(within(unplaced).getByRole("img")).toHaveAccessibleName(PEG.empty);
    expect(unplaced).toHaveTextContent(CANNOT_PLACE);
  });

  test("test_the_key_says_what_the_page_says_of_a_band_and_states_no_figure_of_its_own", () => {
    const said = [ABOUT.band.lead, ABOUT.band.pictures, ...Object.values(ABOUT.band.states)].join(" ");

    // The page says when an area is mixed, and that one that cannot be placed is never put in the
    // middle. The key says both of what is seen: it speaks of steps, where the page speaks of bands.
    expect(VIBES.how.points.join(" ")).toContain("span three bands or more");
    expect(ABOUT.band.states.mixed).toContain("span three steps or more");
    expect(VIBES.how.points.join(" ")).toContain("never puts it in the middle");
    expect(ABOUT.band.states.unplaced).toContain("never draws such an area in the middle");
    expect(/\d/.test(said)).toBe(false);
    // A band is a taste and never a score: no word of the key says that more is better, or that anything is won.
    expect(/%|percent|score|\brank|\bbest\b|\bworst\b|\bwin|\bprize|\bstars?\b/i.test(said)).toBe(false);
    expect(ABOUT.band.lead).toContain("and not that the area is better");
  });

  test("test_what_it_says_of_an_area_that_cannot_be_placed_is_true_however_its_steps_are_edged", () => {
    // The founder: "The dashed border is not understood to a user". The steps of such an
    // area are said to be empty and to bear no peg, which is so whatever edge they are given.
    expect(/dash|dot/i.test(Object.values(ABOUT.band.states).join(" "))).toBe(false);
    expect(ABOUT.band.states.unplaced).toMatch(/^Five empty steps with no peg/);
  });

  test("test_nothing_of_the_key_moves_or_can_be_pressed", () => {
    const { container } = render(<BandKey meta={meta} />);

    expect(container.querySelectorAll("a, button, input, select, textarea, summary, [tabindex]")).toHaveLength(0);
    expect(SHEET.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition|transform)/.test(property)))).toEqual([]);
    expect(SHEET.filter((rule) => /:(hover|focus|active)/.test(rule.selector))).toEqual([]);
  });

  test.each(PAIRS_MAY_STAND)("test_it_has_no_accessibility_fault: %s", async (pairs) => {
    const { container } = render(
      <main>
        <h1>{VIBES.title}</h1>
        <h2>{ABOUT.key.title}</h2>
        <BandKey meta={meta} pairs={pairs} />
      </main>,
    );

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});
