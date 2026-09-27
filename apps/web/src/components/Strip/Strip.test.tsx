import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { BAND_ON_A_SCALE, BAND_ONE_WAY, BAND_VARIES, RESTS_ON } from "@/content/bands";
import { CARD } from "@/content/card";
import { KNOWN, PEG } from "@/content/kit";
import { BREAKDOWN, JOURNEYS, STRIP } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Fact, StripMark, Tag } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { rowOf, setAt } from "../../../test/support/cascade";
import { heavier, rulesOf, weightOf } from "../../../test/support/css";
import { figuresNotFrom } from "../../../test/support/figures";
import { ROUGH } from "../../../test/support/rough";
import { endsOf, inWords } from "@/lib/vibes";

import { sizeOf } from "../kit/drawings";
import { HIGH } from "../Track/Track";
import { picturesAtEnds } from "../kit/Ends/picture";
import { drawingOf } from "../kit/Thing/drawn";
import { asLines, namesOf } from "./column";
import { BEFORE_THE_TWO_WORDS, isFromPart, Picture, picturesOfAMeasure, Strip, UNDER_A_NAME, type Asked } from "./Strip";

/** Whose strip it is, to name it. No test here is about a place, so none is named. */
const OF = "an area";

const meta = recordedAnswer("get_meta", "meta").body.data;
const calm = recordedAnswer("rank", "rank-scale").body.data;
const reasons = recordedAnswer("explain_top", "explanations-scale").body.data;
const facts: Record<string, Fact> = Object.fromEntries(reasons.facts.map((fact) => [fact.fact_id, fact]));

const first = calm.ranked[0];
if (first === undefined) throw new Error("The recording holds no result.");

/** The result whose strip holds a mark drawn as a range. */
const mixed = calm.ranked.find((area) => area.strip.some((mark) => mark.spread_high - mark.spread_low >= 2));
if (mixed === undefined) throw new Error("The recording holds no mixed area.");

const SHEET = readFileSync(path.join(__dirname, "Strip.module.css"), "utf8");
const RULES = rulesOf(SHEET);
const at = (selector: string, under: string | null = null) =>
  new Map(RULES.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));
const WIDE = "@container (min-width: 37.5rem)";
const NARROW = "@container (max-width: 30rem)";
/** A result narrower than a phone gives, which has not the room of a name and a gauge side by side. */
const NO_ROOM = "@container (max-width: 21.2rem)";
/** The width of a result in a window 320 px wide, and in one 360 px wide, which is the narrowest phone that is common. */
const [AT_320, AT_360] = [19, 21.5];

const tagOf = (tagId: string) => meta.tags.find((tag) => tag.tag_id === tagId) as Tag;
const markOf = (tagId: string, marks: readonly StripMark[] = first.strip) =>
  marks.find((mark) => mark.tag_id === tagId) as StripMark;
/** What a list of a strip may be named, of an area: each says what it holds. */
const listsOf = (of: string) => [STRIP.askedOf(of), STRIP.restOf(of), STRIP.othersOf(of), STRIP.label(of)];
/**
 * The lines of a strip, in the order they stand in: of what was asked for, and then of the
 * vibes nobody asked for. Every list of the strip is named for the area and for what it holds.
 */
const lines = (of: string = OF) =>
  screen.getAllByRole("list").flatMap((list) => {
    expect(listsOf(of)).toContain(list.getAttribute("aria-label"));
    return within(list).getAllByRole("listitem");
  });
/** What holds every list of a strip, and is told what stands in the column of names. */
const holds = () => screen.getAllByRole("list")[0]?.parentElement as HTMLElement;
/** What the picture of a mark says in words, to someone who cannot see it. */
const pictureIn = (mark: HTMLElement | undefined) =>
  within(mark as HTMLElement).getByRole("img").getAttribute("aria-label") ?? "";
/** What a mark says to a screen reader: its words, with each picture said by its name. */
function heardIn(mark: HTMLElement | undefined): string {
  const copy = (mark as HTMLElement).cloneNode(true) as HTMLElement;
  copy.querySelectorAll("[aria-hidden='true']").forEach((drawn) => drawn.remove());
  copy.querySelectorAll("[role='img']").forEach((picture) => picture.replaceWith(` ${picture.getAttribute("aria-label")} `));
  return (copy.textContent ?? "").replace(/\s+/g, " ").trim();
}
/** The pictures a line draws at the two ends of its gauge, by where each is served from. */
const endsIn = (mark: HTMLElement | undefined) =>
  [...(mark as HTMLElement).querySelectorAll<HTMLElement>("[class*='end'] > [aria-hidden='true']")].map((one) =>
    one.style.getPropertyValue("--art"),
  );
const served = (name: string) => `url("/art/${name}.png")`;
/** A mark of a vibe in one band, as the service would send it. */
const inBand = (tag: Tag, band: number, more: Partial<StripMark> = {}) =>
  ({ ...markOf("pace"), tag_id: tag.tag_id, band, spread_low: band, spread_high: band, asked: false, toward: null, ...more }) as StripMark;
/** The facts of the first result, with one of them changed. */
const withFact = (factId: string, slots: Record<string, string>): Record<string, Fact> => {
  const fact = facts[factId];
  if (fact === undefined) throw new Error("The fact of the mark is not in hand.");
  return { ...facts, [factId]: { ...fact, slots: { ...fact.slots, ...slots } } };
};
const clause = "Worked out from 3 of its 5 parts, 70 of 100 by weight.";

/** A measure of the release, by the id the service gives it. */
const metricOf = (featureId: string) => {
  const metric = meta.features.find((one) => one.feature_id === featureId);
  if (metric === undefined) throw new Error("The recorded release holds no such measure.");
  return metric;
};
/** What a measure is drawn by: the family the service puts it in. */
const thingOf = (featureId: string) => ({ kind: "feature", id: featureId, family: metricOf(featureId).family }) as const;
/** A place of the release, as an answer names it. No test here is about a place, so none is written down. */
const [PLACE] = recordedAnswer("rank", "rank-first").body.data.places.map((place) => place.name);
if (PLACE === undefined) throw new Error("The recording names no place.");
/** Where an area stands on a measure, in the words a fact of the service says it in. */
const stood = recordedAnswer("get_area", "area").body.data.facts.find((fact) => fact.kind === "feature" && fact.slots.standing !== undefined);
if (stood === undefined) throw new Error("The recorded profile holds no fact of a measure.");
const STANDS = `${stood.slots.value}, ${stood.slots.standing}`;
/** A line of each kind that is no vibe: a measure with its gauge, a journey, an estimate of one, and a budget. */
const MEASURED: Asked = {
  key: "measure",
  name: metricOf("park_proximity").short_label,
  thing: thingOf("park_proximity"),
  known: "whole",
  gauge: { placed: { band: 4, spread_low: 4, spread_high: 4 }, says: STANDS },
};
const JOURNEY: Asked = { key: "journey 0", name: PLACE, thing: { kind: "place" }, known: "whole", figure: JOURNEYS.minutes(21), side: CARD.side.within };
const ESTIMATED: Asked = { key: "journey 1", name: PLACE, thing: { kind: "place" }, known: "some", figure: JOURNEYS.estimated.borderline };
const BUDGET: Asked = { key: "budget", name: BREAKDOWN.budget, thing: { kind: "budget" }, known: "whole", figure: CARD.cost("1,300", true), side: CARD.side.over };
const UNKNOWN: Asked = { key: "journey 2", name: PLACE, thing: { kind: "place" }, known: "none" };
const EVERY_KIND: readonly Asked[] = [MEASURED, JOURNEY, ESTIMATED, BUDGET, UNKNOWN];

describe("a vibe the service calls a rough guide, on a result", () => {
  // The founder, who had walked the website twice: "remove the concept of rough guide, we
  // don't want to pass this on to a user". The service still says which vibe it holds to be
  // less sure than the rest, in a code. A strip is handed the vibes of the release and
  // nothing else of it, so no word of a service reaches it: it is held to write none of its
  // own, neither the label a service gave such a vibe nor the sentence that said why.
  const asked = recordedAnswer("rank", "rank-rough-guide").body.data;
  const [top] = asked.ranked;
  if (top === undefined) throw new Error("The recording holds no result.");
  const guide = meta.tags.find((tag) => tag.tag_id === ROUGH.tag_id);
  if (guide === undefined) throw new Error("The recorded release holds no such vibe.");

  test("test_the_service_says_which_vibe_it_is_and_a_result_shows_it_where_it_was_asked_for", () => {
    expect(guide.sureness).toBe("rough_guide");
    for (const area of asked.ranked) {
      for (const mark of area.strip.filter((one) => one.tag_id === guide.tag_id)) expect(mark.asked).toBe(true);
    }
    expect(top.strip.map((mark) => mark.tag_id)).toContain(guide.tag_id);
    // Asked for nothing of the kind, no result of any search shows it.
    for (const area of calm.ranked) expect(area.strip.map((mark) => mark.tag_id)).not.toContain(guide.tag_id);
  });

  test("test_its_mark_is_drawn_as_the_mark_of_any_vibe_is_and_nothing_says_that_it_is_a_rough_guide", () => {
    const { container } = render(<Strip marks={top.strip} tags={meta.tags} of="Wickerford" />);
    const marks = lines("Wickerford");
    const mark = marks.find((one) => one.textContent?.includes(guide.label));
    const placed = top.strip.find((one) => one.tag_id === guide.tag_id);
    if (mark === undefined || placed === undefined) throw new Error("The strip draws no mark of the vibe.");

    // Its name, where the area sits on it, and that it was asked for: what is said of any vibe.
    const [low, high] = endsOf(guide);
    expect(heardIn(mark)).toBe(`${guide.label} ${inWords(placed)}, ${STRIP.from(low, high)}, ${STRIP.asked}`);
    // Neither its label nor the sentence that said why stands anywhere in the strip.
    expect(container.querySelector("[data-rough-guide]")).toBeNull();
    expect(container.textContent?.includes(ROUGH.label)).toBe(false);
    expect(container.textContent?.includes(ROUGH.why)).toBe(false);
    expect(/rough|less sure/i.test(container.textContent ?? "")).toBe(false);
    // Every mark of the strip is laid out one way: nothing is added to the line of this one.
    const partsOf = (one: HTMLElement) => [...one.querySelectorAll("*")].map((part) => `${part.tagName} ${part.className}`);
    const other = marks.find((one) => one !== mark && one.getAttribute("data-asked") === "true" && !one.textContent?.includes(STRIP.group.asked));
    if (other !== undefined) expect(partsOf(mark).filter((part) => !/group/.test(part))).toEqual(partsOf(other));
  });

  test("test_the_strip_is_handed_nothing_a_rough_guide_says_of_itself_and_reads_no_word_of_one", () => {
    // What the service says of a rough guide is no part of what a strip is handed, and the
    // part that drew its label and its note is not read here.
    const written = ["Strip.tsx", "Strip.module.css"].map((file) => readFileSync(path.join(__dirname, file), "utf8")).join("\n");

    expect(/rough|sureness|RoughGuide/i.test(written)).toBe(false);
  });
});

describe("the lines of a result", () => {
  test("test_each_line_is_named_by_the_api_and_its_picture_says_its_band_in_words", () => {
    render(<Strip marks={first.strip} tags={meta.tags} of={OF} />);
    const marks = lines();

    expect(marks).toHaveLength(first.strip.length);
    first.strip.forEach((mark, at) => {
      const label = meta.tags.find((tag) => tag.tag_id === mark.tag_id)?.label ?? "";
      expect(marks[at]).toHaveTextContent(label);
      expect(pictureIn(marks[at])).toContain(STRIP.band(mark.band));
    });
  });

  test("test_no_word_stands_under_a_gauge_or_beside_one_whatever_the_band", () => {
    // The founder, who had walked the website three times: "remove the explainer text under
    // the gauges. we dont need that level of detail." A line said where the area sits in
    // words, "around the middle" and "at the Newer end", after the steps that show it. The
    // gauge says where the area sits.
    const bands = [1, 2, 3, 4, 5] as const;
    for (const tag of [tagOf("leafy"), tagOf("pace")]) {
      for (const band of bands) {
        const { container, unmount } = render(<Strip marks={[inBand(tag, band)]} tags={meta.tags} of={OF} />);

        // All that is written on a line is what the line is of.
        expect([tag.tag_id, band, container.textContent]).toEqual([tag.tag_id, band, tag.label]);
        unmount();
      }
    }
    const wide = { ...inBand(tagOf("leafy"), 5), spread_low: 3, spread_high: 5 };
    const { container } = render(<Strip marks={[wide]} tags={meta.tags} of={OF} />);
    expect(container.textContent).toBe(tagOf("leafy").label);
    // No word for a band is written into what draws a line.
    const written = ["Strip.tsx", "Strip.module.css"].map((file) => readFileSync(path.join(__dirname, file), "utf8")).join("\n");
    const words = [...Object.values(BAND_ONE_WAY), ...bands.map((band) => BAND_ON_A_SCALE[band]("", "").trim()), BAND_VARIES];
    expect(words.filter((word) => word !== "" && written.includes(word))).toEqual([]);
    expect(/plainly|BAND_/.test(written)).toBe(false);
  });

  test("test_whoever_hears_the_page_is_still_told_in_words_where_the_area_sits", () => {
    // What is taken from sight is not taken from what is heard: the picture of a line is
    // named by the band, and by the two ends the bands run between.
    render(<Strip marks={first.strip} tags={meta.tags} of={OF} />);
    const marks = lines();

    first.strip.forEach((mark, at) => {
      const tag = tagOf(mark.tag_id);
      const picture = within(marks[at] as HTMLElement).getByRole("img");
      const [low, high] = endsOf(tag);

      expect(picture.getAttribute("aria-label")).toContain(STRIP.from(low, high));
      expect(picture.getAttribute("aria-label")).toContain(inWords(mark));
      // The picture holds no word: it is a picture, and its name is what is heard.
      expect(picture.textContent).toBe("");
      // The steps themselves are kept from a screen reader: the picture they stand in is what is named.
      expect(picture.querySelector("[data-on]")?.parentElement).toHaveAttribute("aria-hidden", "true");
      // A line is heard as its name and its picture, and as nothing more.
      expect(heardIn(marks[at])).toBe(`${tag.label} ${picture.getAttribute("aria-label")}`);
    });
  });

  test("test_the_picture_of_a_mark_says_what_it_shows_and_nothing_is_kept_for_a_screen_reader_alone", () => {
    const { container } = render(<Strip marks={first.strip} tags={meta.tags} of={OF} />);

    // The band is drawn, and the drawing is named. It is not a sentence hidden from the eye.
    expect(container.querySelectorAll(".visually-hidden")).toHaveLength(0);
    // What is kept from a screen reader holds no word that is not said elsewhere on its line.
    for (const drawn of container.querySelectorAll("[aria-hidden='true']")) {
      const said = pictureIn(drawn.closest("li") as HTMLElement);
      const word = drawn.textContent ?? "";
      expect(word === "" || word === STRIP.group.also || said.toLowerCase().includes(word.toLowerCase())).toBe(true);
    }
    expect(screen.getAllByRole("img")).toHaveLength(first.strip.length);
  });

  test("test_a_scale_says_both_its_ends_and_the_one_asked_for_in_the_name_of_its_picture", () => {
    render(<Strip marks={first.strip} tags={meta.tags} of={OF} />);
    const pace = lines()[0] as HTMLElement;

    expect(markOf("pace")).toMatchObject({ asked: true, toward: "low" });
    expect(pictureIn(pace)).toBe(
      `${STRIP.band(markOf("pace").band)}, ${STRIP.from("Calm", "Buzzy")}, ${STRIP.askedFor("Calm")}`,
    );
  });

  test("test_a_mark_is_heard_as_one_phrase_in_which_no_end_is_said_twice", () => {
    // Heard in a browser: "asked for: Buzzy Buzzy". The name of the end that was asked for
    // was said by the picture, and then again by the word drawn after it.
    const buzzy = recordedAnswer("rank", "rank-scale-turned").body.data.ranked[0]?.strip ?? [];
    render(<Strip marks={buzzy} tags={meta.tags} of="Pellam Cross" />);
    const pace = lines("Pellam Cross")[0] as HTMLElement;

    expect(markOf("pace", buzzy)).toMatchObject({ asked: true, toward: "high", band: 5 });
    expect(heardIn(pace)).toBe(`Going out ${STRIP.band(5)}, ${STRIP.from("Calm", "Buzzy")}, ${STRIP.askedFor("Buzzy")}`);
    expect(heardIn(pace).split("Buzzy")).toHaveLength(3);
  });

  test("test_a_vibe_that_runs_one_way_says_the_end_an_area_sits_at_once_to_a_screen_reader", () => {
    // Recorded: one result sits at the least of a vibe that was asked for, and at the most of
    // one that was not.
    const ranked = recordedAnswer("rank", "rank-first").body.data.ranked;
    const marks = ranked.find((area) => area.area_id === "syn-n0004")?.strip ?? [];
    render(<Strip marks={marks} tags={meta.tags} of="Dulcimer Green" />);
    const drawn = (label: string) => lines("Dulcimer Green").find((mark) => mark.textContent?.includes(label));
    const [quiet, family] = [drawn("Quiet streets"), drawn("Family amenities")];

    expect(markOf("quiet_residential", marks)).toMatchObject({ asked: true, band: 1 });
    expect(markOf("family_amenities", marks)).toMatchObject({ asked: false, band: 5 });
    expect(heardIn(quiet)).toBe(`Quiet streets ${STRIP.band(1)}, ${STRIP.from(STRIP.least, STRIP.most)}, ${STRIP.asked}`);
    expect(heardIn(family)).toBe(`Family amenities ${STRIP.band(5)}, ${STRIP.from(STRIP.least, STRIP.most)}`);
  });

  test("test_a_vibe_nobody_asked_for_is_never_drawn_at_its_least", () => {
    // Seen in a browser: the first result opened with two vibes nobody had asked for, each at
    // "least". They read as two warnings on the best answer. The API no longer sends such a mark.
    const oneWay = new Set(meta.tags.filter((tag) => tag.shape === "one_way").map((tag) => tag.tag_id));
    const others = (["rank-first", "rank-money-and-work", "rank-two-journeys", "rank-default-rent"] as const)
      .flatMap((scenario) => recordedAnswer("rank", scenario).body.data.ranked)
      .flatMap((area) => area.strip.filter((mark) => !mark.asked));

    expect(others.length).toBeGreaterThan(20);
    expect(others.filter((mark) => oneWay.has(mark.tag_id) && mark.band < 4)).toEqual([]);
  });

  test("test_that_lines_were_asked_for_is_said_for_the_eye_only_where_a_line_beside_them_was_not", () => {
    const four = recordedAnswer("rank", "rank-first").body.data.ranked[0]?.strip ?? [];
    const { unmount } = render(<Strip marks={four} tags={meta.tags} of="Farrowmere" />);
    const groupsOf = () =>
      lines("Farrowmere").map((mark) => mark.querySelector("[class*='group'][aria-hidden='true']")?.textContent ?? null);

    expect(four.map((mark) => mark.asked)).toEqual([true, true, false, false]);
    // For the eye: once before the first that was asked for, and once before the first that was not.
    expect(groupsOf()).toEqual([STRIP.group.asked, null, STRIP.group.also, null]);
    // For a screen reader: of each mark that was asked for, and of no other.
    expect(lines("Farrowmere").map((mark) => pictureIn(mark).endsWith(STRIP.asked))).toEqual([true, true, false, false]);
    unmount();

    // Where every line was asked for, or none was, nothing tells one kind from another:
    // a line is its name, its gauge and no more.
    for (const kept of [true, false]) {
      const some = four.filter((mark) => mark.asked === kept);
      const drawn = render(<Strip marks={some} tags={meta.tags} of="Farrowmere" />);
      expect(some).toHaveLength(2);
      expect(groupsOf()).toEqual([null, null]);
      expect(drawn.container.textContent?.includes(STRIP.group.asked)).toBe(false);
      expect(drawn.container.textContent?.includes(STRIP.group.also)).toBe(false);
      // Whoever hears the page is told of each line all the same.
      expect(lines("Farrowmere").map((mark) => pictureIn(mark).endsWith(STRIP.asked))).toEqual([kept, kept]);
      drawn.unmount();
    }
  });

  test("test_a_vibe_that_runs_one_way_is_counted_from_least_to_most", () => {
    const leafy = recordedAnswer("rank", "rank-shelf").body.data.ranked[0];
    render(<Strip marks={leafy?.strip ?? []} tags={meta.tags} of="Brackenhythe" />);

    expect(pictureIn(lines("Brackenhythe")[0])).toContain(STRIP.from(STRIP.least, STRIP.most));
    expect(pictureIn(lines("Brackenhythe")[0])).toContain(STRIP.asked);
  });

  test("test_a_mixed_area_is_drawn_as_a_rail_and_sits_at_neither_end", () => {
    const oneWay = meta.tags.find((tag) => tag.shape === "one_way") as Tag;
    const mixedUp = { ...inBand(oneWay, 5), spread_low: 3, spread_high: 5 };
    const { container } = render(<Strip marks={[mixedUp]} tags={meta.tags} of="Anywhere" />);

    expect(container.textContent).toBe(oneWay.label);
    expect(pictureIn(lines("Anywhere")[0])).toBe(`${STRIP.bands(3, 5)}, ${STRIP.from(STRIP.least, STRIP.most)}`);
    // No peg stands on any one step: a rail joins the steps it spans.
    expect(container.querySelector("[class*='peg']")).toBeNull();
    expect(container.querySelectorAll("[class*='rail']")).toHaveLength(1);
  });

  test("test_the_words_for_the_ends_of_a_one_way_vibe_are_the_ones_the_api_uses", () => {
    const oneWay = new Set(meta.tags.filter((tag) => tag.shape === "one_way").map((tag) => tag.tag_id));
    const said = reasons.facts.filter((fact) => fact.kind === "tag" && oneWay.has(fact.key as never));

    expect(said.length).toBeGreaterThan(0);
    for (const fact of said) {
      expect([fact.slots.low_end, fact.slots.high_end]).toEqual([STRIP.least, STRIP.most]);
    }
    const scale = meta.tags.find((tag) => tag.shape === "scale");
    expect(endsOf(scale as never)).toEqual([scale?.low_end, scale?.high_end]);
  });

  test("test_the_strip_draws_every_mark_it_is_handed_at_every_width_and_hides_none", () => {
    // Which vibes a result draws is the page's to choose, and is chosen for every screen
    // alike. A style sheet once took the vibes nobody asked for off a narrow screen, so
    // that a phone and a desk drew two results of one answer.
    const four = recordedAnswer("rank", "rank-first").body.data.ranked[1]?.strip ?? [];
    render(<Strip marks={four} tags={meta.tags} of="Farrowmere" />);

    expect(four.map((mark) => mark.asked)).toEqual([true, true, false, false]);
    expect(lines("Farrowmere").map((item) => item.getAttribute("data-asked"))).toEqual(["true", "true", "false", "false"]);
    // Nothing is taken off a result by its width but what one press of the result shows
    // again: the lines that a narrow result folds, and on a wide one the press itself.
    expect(RULES.filter((rule) => rule.sets.get("display") === "none").map((rule) => [rule.under, rule.selector])).toEqual([
      [null, ".fold"],
      [NARROW, '.lines[data-folded="true"]'],
    ]);
    expect(at(".fold", NARROW).get("display")).toBe("block");
    // No line that a vibe nobody asked for stands on is ever folded, and none that was is told from one that was not.
    expect(RULES.filter((rule) => /data-asked/.test(rule.selector) && rule.sets.has("display"))).toEqual([]);
    expect(RULES.filter((rule) => /^@media/.test(rule.under ?? "") && !/forced-colors/.test(rule.under ?? ""))).toEqual([]);
  });

  test("test_a_mixed_area_is_a_range_and_never_a_point_in_the_middle", () => {
    const mark = mixed.strip.find((one) => one.spread_high - one.spread_low >= 2) as StripMark;
    const { container } = render(<Strip marks={[mark]} tags={meta.tags} of="Foxholt" />);

    expect(inWords(mark)).toBe(STRIP.bands(mark.spread_low, mark.spread_high));
    expect(pictureIn(screen.getByRole("listitem"))).toContain(STRIP.bands(mark.spread_low, mark.spread_high));
    const filled = [...container.querySelectorAll("[data-on='true']")];
    expect(filled).toHaveLength(mark.spread_high - mark.spread_low + 1);
  });

  test("test_a_vibe_the_release_does_not_name_is_left_out", () => {
    const stranger = { ...markOf("pace"), tag_id: "not_a_vibe" } as unknown as StripMark;
    render(<Strip marks={[stranger, markOf("pace")]} tags={meta.tags} of={OF} />);

    expect(screen.getAllByRole("listitem")).toHaveLength(1);
  });

  test("test_with_nothing_to_draw_there_is_no_strip", () => {
    const { container } = render(<Strip marks={[]} tags={meta.tags} of={OF} />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_no_line_opens_and_no_key_of_a_source_stands_on_one_though_its_fact_is_in_hand", () => {
    // The founder: "the source's key should just exist under the show the working section
    // we dont need it at the summary high level card version". A line opened to its fact,
    // with its source. The fact is in the working of the result, one press away.
    const { container } = render(<Strip marks={first.strip} tags={meta.tags} facts={facts} of={OF} />);

    expect(first.strip.every((mark) => facts[mark.fact_id] !== undefined)).toBe(true);
    expect(container.querySelectorAll("button, a, [tabindex], details, summary")).toHaveLength(0);
    expect(container.querySelector("[style*='ui-key']")).toBeNull();
    // Every figure a line shows is none: what is drawn is a band, which its picture names.
    expect(figuresNotFrom(container, new Set(first.strip.map(inWords)))).toEqual([]);
  });

  test("test_the_strip_has_no_fault_an_automated_check_can_find", async () => {
    const { container } = render(
      <Strip
        marks={first.strip}
        tags={meta.tags}
        facts={withFact(first.strip[0]?.fact_id ?? "", { known: "3", parts: "5" })}
        unplaced={["leafy"]}
        asked={EVERY_KIND}
        fold={{ over: 3, most: 4 }}
        of={OF}
      />,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("a picture at each end of every gauge, and the drawing of the vibe with its name", () => {
  // The founder, who had walked the website three times: "Add any icon to the relevent
  // gauge, for example, you have an icon for leafy and calm, but they are not in next the
  // relevent gauge, where a gauge may exist, ensure they have a opposing icons for each
  // side of the gauge." And: "show only one example of house or flat type at either side
  // of the gauge, this will help add space."
  const everyVibe = meta.tags.map((tag) => inBand(tag, 3));

  test("test_each_end_of_every_gauge_has_one_picture_which_is_chosen_by_the_id_of_its_vibe", () => {
    render(<Strip marks={everyVibe} tags={meta.tags} of={OF} />);
    const marks = lines();

    expect(marks.length).toBe(meta.tags.length);
    expect(meta.tags.some((tag) => tag.shape === "one_way")).toBe(true);
    meta.tags.forEach((tag, at) => {
      // A scale and a vibe that runs one way alike: one picture at the low end, and one at the high.
      const [low, high] = picturesAtEnds(tag.tag_id);
      expect([tag.tag_id, endsIn(marks[at])]).toEqual([tag.tag_id, [served(low), served(high)]]);
      // The two are opposites, and so are two pictures and never one drawn twice.
      expect([tag.tag_id, low === high]).toEqual([tag.tag_id, false]);
      // Between them stand the steps.
      const inside = [...(marks[at]?.querySelector("[role='img']") as HTMLElement).children].map((part) => part.className.split(" ")[0]);
      expect(inside).toEqual(["end", "track", "end"]);
    });
  });

  test("test_the_picture_of_an_end_is_dress_of_one_size_and_neither_end_is_marked_as_the_better", () => {
    const { container } = render(<Strip marks={first.strip} tags={meta.tags} of={OF} />);
    const ends = [...container.querySelectorAll<HTMLElement>(".end")];

    expect(ends).toHaveLength(first.strip.length * 2);
    for (const end of ends) {
      const drawn = end.firstElementChild as HTMLElement;
      // It is kept from whoever hears the page, inside the picture that says both ends in words.
      expect(drawn).toHaveAttribute("aria-hidden", "true");
      expect(end.closest("[role='img']")).not.toBeNull();
      expect(end.textContent).toBe("");
      expect([drawn.style.getPropertyValue("--w"), drawn.style.getPropertyValue("--h")]).toEqual(["16", "16"]);
    }
    // The two ends are laid out alike: no rule of the sheet is of one end and not of the
    // other but the one that says at which side it stands.
    const ofOneEnd = RULES.filter((rule) => /\.end(:(first|last)-child| ~ \.end)/.test(rule.selector));
    expect(ofOneEnd.map((rule) => [rule.selector, [...rule.sets.keys()]])).toEqual([[".end ~ .end > *", ["grid-column"]]]);
    // Nothing of a line is red, and nothing is dimmed.
    expect(SHEET).not.toMatch(/poppy|tradeoff|--error|--good|opacity/);
  });

  test("test_a_vibe_nobody_has_drawn_has_the_blank_picture_at_both_its_ends_and_is_never_drawn_with_none", () => {
    const stranger: Tag = { ...tagOf("pace"), tag_id: "not_yet_drawn" as Tag["tag_id"], label: "A vibe nobody drew" };
    render(<Strip marks={[inBand(stranger, 2)]} tags={[stranger]} of={OF} />);

    expect(endsIn(screen.getByRole("listitem"))).toEqual([served("end-blank"), served("end-blank")]);
    expect(screen.getByRole("img")).toHaveAccessibleName(`${STRIP.band(2)}, ${STRIP.from("Calm", "Buzzy")}`);
  });

  test("test_the_small_drawing_of_a_vibe_stands_with_its_name_and_is_chosen_by_the_id_the_service_gives", () => {
    render(<Strip marks={everyVibe} tags={meta.tags} of={OF} />);
    const marks = lines();

    meta.tags.forEach((tag, at) => {
      const title = marks[at]?.querySelector("[class*='title']") as HTMLElement;
      const drawn = title.querySelector<HTMLElement>("[aria-hidden='true'] > span");
      const name = title.querySelector("[class*='name']");

      expect(drawn?.style.getPropertyValue("--art")).toBe(served(drawingOf({ kind: "tag", id: tag.tag_id, family: tag.family })));
      expect(name?.textContent).toBe(tag.label);
      // The drawing comes before the name, in one cell, and is dress: the name is what is read.
      expect(title.firstElementChild?.contains(drawn)).toBe(true);
      expect(drawn?.closest("[aria-hidden='true']")).not.toBeNull();
    });
    // It is drawn at two pixels of the screen to one of its own on every screen, as the
    // pictures of the two ends are.
    expect(at(".thing").get("--px")).toBe("var(--px-ground)");
    expect(at(".end").get("--px")).toBe("var(--px-ground)");
    expect(sizeOf("end-blank")).toEqual({ width: 16, height: 16 });
  });

  test("test_one_line_of_the_look_names_the_two_ends_under_the_gauge_and_the_picture_says_what_it_said", () => {
    const { unmount } = render(<Strip marks={first.strip} tags={meta.tags} of={OF} />);
    const pictured = lines().map((mark) => [endsIn(mark), pictureIn(mark)]);
    expect(holds()).toHaveAttribute("data-ends", "pictured");
    expect(document.querySelectorAll("[class*='ofEnd'], [class*='named']")).toHaveLength(0);
    unmount();
    render(<Strip marks={first.strip} tags={meta.tags} of={OF} ends="named" />);
    const marks = lines();

    expect(holds()).toHaveAttribute("data-ends", "named");
    // Each end has its picture as it had, and the picture says what it said.
    expect(marks.map((mark) => [endsIn(mark), pictureIn(mark)])).toEqual(pictured);
    first.strip.forEach((mark, at) => {
      const named = [...(marks[at] as HTMLElement).querySelectorAll("[class*='ofEnd']")].map((one) => one.textContent);
      expect(named).toEqual([...endsOf(tagOf(mark.tag_id))]);
      // The names are drawn for the eye, inside the picture that says them to whoever hears the page.
      const gauge = within(marks[at] as HTMLElement).getByRole("img");
      expect([...gauge.children].map((part) => part.className.split(" ")[0])).toEqual(["end", "track", "end", "named"]);
    });
    // The end that was asked for is named heavier, and the name of the picture says which it is.
    const pace = marks[0] as HTMLElement;
    expect([...pace.querySelectorAll("[class*='ofEnd'][data-asked='true']")].map((end) => end.textContent)).toEqual(["Calm"]);
    expect([...pace.querySelectorAll("[class*='ofEnd'][data-asked='false']")].map((end) => end.textContent)).toEqual(["Buzzy"]);
    expect(at('.ofEnd[data-asked="true"]').get("font-weight")).toBe("700");
    // The two names stand under the gauge, from edge to edge of it, each at its own end: so a
    // name has the room of half a gauge, and is not broken letter by letter under a picture
    // that is narrower than it. Seen in a browser: "New", and under it "er".
    const names = at(".picture > .named");
    expect([names.get("grid-row"), names.get("grid-column"), names.get("display"), names.get("justify-content")]).toEqual([
      "2",
      "1 / -1",
      "flex",
      "space-between",
    ]);
    expect(at(".ofEnd").get("overflow-wrap")).toBe("break-word");
    expect(at(".ofEnd:last-child").get("text-align")).toBe("end");
    // The steps stay on the line of the pictures, and the room of an end is as it was.
    expect(RULES.filter((rule) => /data-ends/.test(rule.selector))).toEqual([]);
  });

  test("test_in_a_list_of_many_small_things_a_line_has_small_steps_and_says_what_it_says_on_a_card", () => {
    const { unmount } = render(<Strip marks={first.strip} tags={meta.tags} of={OF} />);
    const onACard = lines().map((mark) => [mark.textContent, pictureIn(mark), endsIn(mark)]);
    unmount();
    const { container } = render(<Strip marks={first.strip} tags={meta.tags} of={OF} short />);

    expect(lines().map((mark) => [mark.textContent, pictureIn(mark), endsIn(mark)])).toEqual(onACard);
    // Small steps, and a cap on the one the area sits on.
    expect(container.querySelectorAll("[data-small='true']")).toHaveLength(first.strip.length);
    expect(holds()).toHaveAttribute("data-short", "true");
  });

  test("test_no_vibe_and_no_end_of_a_scale_is_written_into_the_strip", () => {
    // A picture is chosen by the id the service gives a vibe. None is written here, so a
    // release that names another vibe draws it, or the blank one, and never the wrong one.
    const written = ["Strip.tsx", "Strip.module.css"].map((file) => readFileSync(path.join(__dirname, file), "utf8")).join("\n");
    const names = [
      ...meta.tags.flatMap((tag) => [tag.label, tag.tag_id, tag.low_end, tag.high_end]),
      ...meta.families.map((family) => family.label),
    ].filter((name): name is string => typeof name === "string" && name !== "");

    expect(names.length).toBeGreaterThan(20);
    expect(names.filter((name) => new RegExp(`["'\`/-]${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["'\`.]`, "i").test(written))).toEqual([]);
    expect(/(key|end|thing|ui)-[a-z]/.test(written)).toBe(false);
  });
});

describe("what is not whole, and what is not known", () => {
  // The founder: "just show the incomplete data icon and simple text of 'approx data'".
  const [mark] = first.strip;
  if (mark === undefined) throw new Error("The recording holds no mark.");

  test("test_a_band_worked_out_from_some_of_what_goes_into_it_says_approx_data_and_nothing_else_of_it", () => {
    const told = withFact(mark.fact_id, { known: "3", parts: "5", share: "70", partly: clause });
    const { container } = render(<Strip marks={[mark]} tags={meta.tags} facts={told} of={OF} />);
    const line = screen.getByRole("listitem");

    // In sight, with nothing pressed, and heard: the two words, after the mark of what is not whole.
    const said = screen.getByText(KNOWN.some);
    expect(said.closest("[role='img'], [aria-hidden='true'], [hidden]")).toBeNull();
    expect(said.previousElementSibling).toHaveAttribute("aria-hidden", "true");
    expect((said.previousElementSibling as HTMLElement).style.getPropertyValue("--art")).toBe(served("ui-approx"));
    expect(line.textContent).toBe(`${tagOf(mark.tag_id).label}${KNOWN.some}`);
    // What it was worked out from is said nowhere on the line: not in the words of the
    // service, not in those of the website, and no count of it.
    expect(screen.queryByText(clause)).toBeNull();
    expect(container.textContent?.includes(RESTS_ON.short("3", "5"))).toBe(false);
    expect(/\d/.test(line.textContent ?? "")).toBe(false);
    // The step the peg stands on is chequered, and the peg stands as it would.
    expect(container.querySelector("[data-part='true'] [data-on='true']")).not.toBeNull();
    expect(container.querySelectorAll("[class*='peg']")).toHaveLength(1);
    expect(line.firstElementChild).toHaveAttribute("data-known", "some");
  });

  test("test_whether_a_band_is_whole_is_read_from_the_two_counts_its_fact_holds_and_nothing_is_added_up", () => {
    const fact = facts[mark.fact_id] as Fact;
    const with_ = (slots: Record<string, string | undefined>) => ({ ...fact, slots: { ...fact.slots, ...slots } }) as Fact;

    expect(isFromPart(with_({ known: "3", parts: "5" }))).toBe(true);
    expect(isFromPart(with_({ known: "5", parts: "5" }))).toBe(false);
    // A fact that does not say is not said to be anything, and a fact that is not in hand neither.
    expect(isFromPart(with_({ known: undefined, parts: undefined }))).toBe(false);
    expect(isFromPart(undefined)).toBe(false);
  });

  test("test_a_band_that_is_whole_or_whose_fact_is_not_in_hand_says_nothing_of_it", () => {
    const whole = withFact(mark.fact_id, { known: "5", parts: "5", share: "100", partly: "" });
    const { container, unmount } = render(<Strip marks={[mark]} tags={meta.tags} facts={whole} of={OF} />);

    expect(container.textContent).toBe(tagOf(mark.tag_id).label);
    expect(container.querySelector("[data-part='true']")).toBeNull();
    expect(screen.getByRole("listitem").firstElementChild).toHaveAttribute("data-known", "whole");
    unmount();
    // A row of results has no fact of its marks in hand: nothing is made up of what they rest on.
    const none = render(<Strip marks={[mark]} tags={meta.tags} of={OF} />);
    expect(none.container.textContent).toBe(tagOf(mark.tag_id).label);
    expect(none.container.querySelector("[data-part='true']")).toBeNull();
  });

  test("test_what_a_band_was_worked_out_from_can_be_left_to_where_its_fact_is_opened", () => {
    const told = withFact(mark.fact_id, { known: "3", parts: "5", share: "70", partly: clause });
    const { container } = render(<Strip marks={[mark]} tags={meta.tags} facts={told} of={OF} rests={false} />);

    expect(screen.queryByText(KNOWN.some)).toBeNull();
    // A step is chequered only where the words that say so stand beside it.
    expect(container.querySelector("[data-part='true']")).toBeNull();
  });

  test("test_a_vibe_that_was_asked_for_and_could_not_be_worked_out_has_its_line_and_is_said_to_be_not_known", () => {
    const leafy = tagOf("leafy");
    const { container } = render(<Strip marks={[mark]} tags={meta.tags} unplaced={[leafy.tag_id]} of={OF} />);
    const [, line] = lines();
    if (line === undefined) throw new Error("The vibe has no line.");

    expect(lines()).toHaveLength(2);
    expect(line.textContent).toBe(`${leafy.label}${KNOWN.none}`);
    expect(screen.getByText(KNOWN.none).closest("[role='img'], [aria-hidden='true'], [hidden]")).toBeNull();
    // Its gauge holds nothing: five empty steps and no peg, with a picture at each end. It
    // is neither put in the middle nor drawn at nought.
    expect(line.querySelectorAll("[data-on]")).toHaveLength(0);
    expect(line.querySelector("[data-placed='false']")).not.toBeNull();
    expect(line.querySelector("[class*='peg'], [class*='rail']")).toBeNull();
    expect(endsIn(line)).toEqual(picturesAtEnds(leafy.tag_id).map(served));
    expect(pictureIn(line)).toBe(PEG.empty);
    expect(heardIn(line)).toBe(`${leafy.label} ${PEG.empty} ${KNOWN.none}`);
    expect(line.firstElementChild).toHaveAttribute("data-known", "none");
    expect(container.querySelector("[data-known='none'] [style*='ui-approx']")).toBeNull();
  });

  test("test_a_vibe_that_has_a_mark_is_drawn_once_and_is_never_also_said_to_be_not_known", () => {
    render(<Strip marks={[mark]} tags={meta.tags} unplaced={[mark.tag_id, "not_a_vibe"]} of={OF} />);

    expect(lines()).toHaveLength(1);
    expect(screen.queryByText(KNOWN.none)).toBeNull();
  });

  test("test_what_else_was_asked_for_and_has_no_figure_has_its_line_after_the_vibes_and_is_said_to_be_not_known", () => {
    const lacked: readonly Asked[] = [UNKNOWN, { key: "budget", name: BREAKDOWN.budget, thing: { kind: "budget" }, known: "none" }];
    const { container } = render(<Strip marks={[mark]} tags={meta.tags} asked={lacked} of={OF} />);
    const [vibe, ...others] = within(screen.getByRole("list", { name: STRIP.askedOf(OF) })).getAllByRole("listitem");

    // It was asked for as the vibe was, and stands in the one list of what was, after the vibes.
    expect(screen.getAllByRole("list")).toHaveLength(1);
    expect(vibe?.textContent).toBe(tagOf(mark.tag_id).label);
    expect(others.map((line) => line.textContent)).toEqual([`${PLACE}${KNOWN.none}`, `${BREAKDOWN.budget}${KNOWN.none}`]);
    // It has the drawing of its kind before its name, and no gauge and no figure: nothing
    // is drawn of a figure that is not known.
    expect(others.map((line) => line.querySelector<HTMLElement>("[class*='title'] [aria-hidden='true'] > span")?.style.getPropertyValue("--art"))).toEqual([
      served(drawingOf({ kind: "place" })),
      served(drawingOf({ kind: "budget" })),
    ]);
    for (const line of others) {
      expect(line.querySelector("[role='img'], [class*='track'], [class*='told']")).toBeNull();
      expect(line.firstElementChild).toHaveAttribute("data-known", "none");
      expect(within(line).getByText(KNOWN.none).closest("[aria-hidden='true'], [hidden]")).toBeNull();
    }
    expect(container.querySelectorAll("button, a")).toHaveLength(0);
    // With nothing else to draw, the list stands alone, and is named for what it holds.
    render(<Strip marks={[]} tags={meta.tags} asked={[UNKNOWN]} of="Elsewhere" />);
    expect(screen.queryByRole("list", { name: STRIP.label("Elsewhere") })).toBeNull();
    expect(within(screen.getByRole("list", { name: STRIP.askedOf("Elsewhere") })).getAllByRole("listitem")).toHaveLength(1);
  });
});

describe("a line for each thing that was asked for", () => {
  // The founder, of a result: "ideally for the break down, we need the info to be title of
  // what was asked for, the visual gauge, and where relevent, the approx data call out". A
  // result drew a line for each vibe that was asked for, and for nothing else that was.
  const [mark] = first.strip;
  if (mark === undefined) throw new Error("The recording holds no mark.");
  const drawingIn = (line: HTMLElement | undefined) =>
    line?.querySelector<HTMLElement>("[class*='title'] [aria-hidden='true'] > span")?.style.getPropertyValue("--art");

  test("test_the_lines_stand_in_one_list_in_the_order_they_are_handed_after_the_vibes_that_were_asked_for", () => {
    const asked = first.strip.filter((one) => one.asked);
    render(<Strip marks={asked} tags={meta.tags} asked={[MEASURED, JOURNEY, BUDGET]} of={OF} />);
    const drawn = within(screen.getByRole("list", { name: STRIP.askedOf(OF) })).getAllByRole("listitem");

    expect(asked.length).toBeGreaterThan(0);
    expect(screen.getAllByRole("list")).toHaveLength(1);
    expect(drawn.map((line) => line.querySelector("[class*='name']")?.textContent)).toEqual([
      ...asked.map((one) => tagOf(one.tag_id).label),
      MEASURED.name,
      JOURNEY.name,
      BUDGET.name,
    ]);
    // Each has the small drawing of what it is before its name.
    expect(drawn.slice(asked.length).map(drawingIn)).toEqual([MEASURED, JOURNEY, BUDGET].map((one) => served(drawingOf(one.thing))));
    expect(drawn.map((line) => line.getAttribute("data-asked"))).toEqual(drawn.map(() => "true"));
  });

  test("test_a_measure_is_a_gauge_of_five_steps_as_a_vibe_is_and_its_picture_says_the_figure_in_the_words_of_the_service", () => {
    const { container } = render(<Strip marks={[mark]} tags={meta.tags} asked={[MEASURED]} of={OF} />);
    const [ofAVibe, ofAMeasure] = lines();
    const gauge = within(ofAMeasure as HTMLElement).getByRole("img");

    // Its steps, its peg and the pictures at its ends are those of any gauge, part for part.
    const partsOf = (line: HTMLElement | undefined) => [...(line?.querySelector("[role='img']") as HTMLElement).querySelectorAll("*")].map((part) => part.className);
    expect(partsOf(ofAMeasure)).toEqual(partsOf(ofAVibe));
    expect(gauge.querySelectorAll("[data-on]")).toHaveLength(5);
    expect([...gauge.querySelectorAll("[data-on]")].map((step) => step.getAttribute("data-on"))).toEqual(["false", "false", "false", "true", "false"]);
    expect(gauge.querySelectorAll("[class*='peg']")).toHaveLength(1);
    // No word stands beside it: what is written on the line is what the line is of.
    expect(ofAMeasure?.textContent).toBe(MEASURED.name);
    expect(container.querySelector("[class*='told']")).toBeNull();
    // Whoever hears the page is told the figure and where it stands, as the service says both.
    expect(gauge).toHaveAccessibleName(STANDS);
    expect(heardIn(ofAMeasure)).toBe(`${MEASURED.name} ${STANDS}`);
    expect(gauge.querySelector("[data-on]")?.parentElement).toHaveAttribute("aria-hidden", "true");
  });

  test("test_a_gauge_of_a_measure_has_the_blank_picture_at_both_ends_until_the_kit_draws_one_for_the_measure_or_for_its_family", () => {
    render(<Strip marks={[]} tags={meta.tags} asked={[MEASURED]} of={OF} />);

    expect(endsIn(screen.getByRole("listitem"))).toEqual([served("end-blank"), served("end-blank")]);
    // Of every measure of the release, and of every family and dimension a measure is drawn by.
    const things = meta.features.map((metric) => ({ id: metric.feature_id, family: metric.family ?? metric.dimension }));
    expect(things.length).toBeGreaterThan(100);
    expect([...new Set(things.flatMap((thing) => picturesOfAMeasure(thing)))]).toEqual(["end-blank"]);
    // A measure is never drawn by the pictures of a vibe, whatever the service calls it.
    for (const tag of meta.tags) {
      expect([tag.tag_id, picturesAtEnds(tag.tag_id).includes("end-blank")]).toEqual([tag.tag_id, false]);
      expect([tag.tag_id, picturesOfAMeasure({ id: tag.tag_id, family: tag.tag_id })]).toEqual([tag.tag_id, ["end-blank", "end-blank"]]);
    }
    expect(picturesOfAMeasure({})).toEqual(["end-blank", "end-blank"]);
  });

  test("test_a_journey_and_a_budget_say_a_figure_and_the_side_it_falls_on_in_a_word_and_no_sentence", () => {
    render(<Strip marks={[]} tags={meta.tags} asked={[JOURNEY, BUDGET]} of={OF} />);
    const [journey, budget] = lines();

    expect(journey?.textContent).toBe(`${PLACE}${JOURNEYS.minutes(21)}${CARD.side.within}`);
    expect(budget?.textContent).toBe(`${BREAKDOWN.budget}${CARD.cost("1,300", true)}${CARD.side.over}`);
    for (const line of [journey, budget]) {
      // No gauge is drawn of a figure that is said, and nothing is kept for a screen reader alone.
      expect(line?.querySelector("[role='img'], [class*='track']")).toBeNull();
      expect(line?.querySelectorAll(".visually-hidden")).toHaveLength(0);
      const told = line?.querySelector("[class*='told']") as HTMLElement;
      expect([...told.children].map((part) => part.className)).toEqual(["figure", "side"]);
      expect(told.closest("[aria-hidden='true']")).toBeNull();
      expect(line?.firstElementChild).toHaveAttribute("data-known", "whole");
    }
    // The side is one word, and neither is drawn as the better: both are ink, the heavier of the line.
    for (const word of Object.values(CARD.side)) expect(word.split(/\s+/)).toHaveLength(1);
    expect(at(".side").get("font-weight")).toBe("700");
    expect([...at(".side").keys()]).toEqual(["font-weight"]);
    expect(at(".told").get("color")).toBe("var(--ink)");
    expect(SHEET).not.toMatch(/poppy|tradeoff|--error|--good|opacity/);
  });

  test("test_a_journey_that_was_estimated_says_approx_data_after_its_mark_and_no_minutes", () => {
    render(<Strip marks={[]} tags={meta.tags} asked={[ESTIMATED]} of={OF} />);
    const line = screen.getByRole("listitem");
    const said = within(line).getByText(KNOWN.some);

    expect(line.textContent).toBe(`${PLACE}${JOURNEYS.estimated.borderline}${KNOWN.some}`);
    expect(/\d/.test(line.textContent ?? "")).toBe(false);
    expect((said.previousElementSibling as HTMLElement).style.getPropertyValue("--art")).toBe(served("ui-approx"));
    expect(said.closest("[role='img'], [aria-hidden='true'], [hidden]")).toBeNull();
    expect(line.firstElementChild).toHaveAttribute("data-known", "some");
  });

  test("test_what_an_area_has_of_a_thing_stands_where_a_gauge_stands_so_that_the_eye_runs_down_one_column", () => {
    // A figure begins where the gauge of the line over it begins, at every width.
    expect([at(".told").get("grid-row"), at(".told").get("grid-column")]).toEqual([at(".picture").get("grid-row"), at(".picture").get("grid-column")]);
    expect([at(".mark > .told", NO_ROOM).get("grid-row"), at(".mark > .told", NO_ROOM).get("grid-column")]).toEqual([
      at(".mark > .picture", NO_ROOM).get("grid-row"),
      at(".mark > .picture", NO_ROOM).get("grid-column"),
    ]);
    expect(at(".mark > .told", NO_ROOM).get("margin-inline-start")).toBe(at(".mark > .picture", NO_ROOM).get("margin-inline-start"));
    const moved = RULES.filter((rule) => /\.told$/.test(rule.selector) && (rule.sets.has("grid-row") || rule.sets.has("grid-column")));
    expect(moved.map((rule) => [rule.under, rule.selector])).toEqual([
      [null, ".told"],
      [NO_ROOM, ".mark > .told"],
    ]);
    // It is read, and is set in the reading face at the size of a small sentence, its figures in columns.
    expect([at(".told").get("font"), at(".told").get("font-variant-numeric")]).toEqual(["400 var(--size-small) / 1.3 var(--font-say)", "tabular-nums"]);
    // A long figure breaks onto a second line, and none is cut.
    expect([at(".told").get("flex-wrap"), at(".told").get("min-width"), at(".told").get("white-space")]).toEqual(["wrap", "0", undefined]);
  });

  test("test_every_line_is_as_high_as_the_line_of_a_gauge_whatever_it_holds", () => {
    // Seen in a browser: the line of a journey stood 12 px lower than the line of a vibe
    // over it, and the line of a measure grew as its gauge came.
    const TRACK = rulesOf(readFileSync(path.join(__dirname, "../Track/Track.module.css"), "utf8"));
    const track = new Map(TRACK.filter((rule) => rule.selector === ".track" && rule.under === null).flatMap((rule) => [...rule.sets]));
    render(<Strip marks={[mark]} tags={meta.tags} asked={[JOURNEY]} of={OF} />);

    // A gauge is as high as the picture at its end, or as its steps with their peg.
    expect(at(".mark").get("min-block-size")).toBe("max(var(--room), calc(var(--px) * var(--steps-high, 0)))");
    expect(at(".strip").get("--room")).toBe(`calc(var(--px-ground) * ${sizeOf("end-blank").height})`);
    // How high the steps are with their peg is told to the sheet by what draws them.
    expect([track.get("--rise"), track.get("--room")]).toEqual(["6", "calc(var(--h) - 3)"]);
    expect(HIGH).toBe(sizeOf("ui-peg").height - 3 + 6);
    expect(holds().style.getPropertyValue("--steps-high")).toBe(String(HIGH));
    // The steps of a list of many small things are lower than the picture at an end.
    expect(at('.strip[data-short="true"] .mark').get("min-block-size")).toBe("var(--room)");
  });
});

describe("a result with no room for every line folds the rest behind one press", () => {
  // Measured at 390 by 844: a line of a result is 38 px high there, and after a sentence of
  // seven things the first result ended under the foot of the first screen.
  const many: readonly Asked[] = [MEASURED, JOURNEY, ESTIMATED, BUDGET, { ...JOURNEY, key: "journey 3" }];
  const FOLD = { over: 3, most: 4 };
  const press = () => screen.getByRole("button");
  const shown = () => within(screen.getByRole("list", { name: STRIP.askedOf(OF) })).getAllByRole("listitem");
  const rest = () => within(screen.getByRole("list", { name: STRIP.restOf(OF) })).getAllByRole("listitem");

  test("test_a_result_of_four_lines_or_fewer_shows_them_all_and_has_no_press", () => {
    for (const count of [1, 2, 3, 4]) {
      const { unmount } = render(<Strip marks={[]} tags={meta.tags} asked={many.slice(0, count)} fold={FOLD} of={OF} />);
      expect([count, shown().length, screen.queryAllByRole("button").length, screen.getAllByRole("list").length]).toEqual([count, count, 0, 1]);
      unmount();
    }
    // Nor has any result that is told of no fold.
    render(<Strip marks={[]} tags={meta.tags} asked={many} of={OF} />);
    expect([shown().length, screen.queryAllByRole("button").length]).toEqual([many.length, 0]);
  });

  test("test_of_more_lines_the_first_stand_over_one_press_that_says_how_many_more_there_are", () => {
    render(<Strip marks={[]} tags={meta.tags} asked={many} fold={FOLD} of={OF} />);

    expect(shown().map((line) => line.querySelector("[class*='name']")?.textContent)).toEqual(many.slice(0, 3).map((one) => one.name));
    expect(rest().map((line) => line.querySelector("[class*='name']")?.textContent)).toEqual(many.slice(3).map((one) => one.name));
    // The press is a native button of the kit. What is seen on it is the start of its name.
    expect(press().tagName).toBe("BUTTON");
    expect(press()).toHaveAccessibleName(CARD.moreOf(CARD.more(2), OF));
    expect(CARD.moreOf(CARD.more(2), OF).startsWith(CARD.more(2))).toBe(true);
    expect(CARD.more(2)).toBe("+2 more");
    // It says that what it shows is put away, and names what it shows.
    expect(press()).toHaveAttribute("aria-expanded", "false");
    expect(press().getAttribute("aria-controls")).toBe(screen.getByRole("list", { name: STRIP.restOf(OF) }).id);
    expect(screen.getByRole("list", { name: STRIP.restOf(OF) })).toHaveAttribute("data-folded", "true");
    // It stands between the lines it follows and the lines it shows, in the order of the page.
    const parts = [...holds().children].map((part) => part.tagName);
    expect(parts).toEqual(["UL", "P", "UL"]);
  });

  test("test_the_lines_over_the_press_may_be_four_and_the_press_then_has_a_row_of_its_own", () => {
    render(<Strip marks={[]} tags={meta.tags} asked={many} fold={{ over: 4, most: 4 }} of={OF} />);

    expect([shown().length, rest().length]).toEqual([4, 1]);
    expect(press()).toHaveAccessibleName(CARD.moreOf(CARD.more(1), OF));
  });

  test("test_the_vibes_that_were_asked_for_are_counted_with_the_rest_and_stand_first", () => {
    const asked = first.strip.filter((one) => one.asked);
    render(<Strip marks={asked} tags={meta.tags} unplaced={["leafy"]} asked={many} fold={FOLD} of={OF} />);

    expect(asked.map((one) => one.tag_id)).toEqual(["pace"]);
    expect(shown().map((line) => line.querySelector("[class*='name']")?.textContent)).toEqual([tagOf("pace").label, tagOf("leafy").label, MEASURED.name]);
    expect(rest()).toHaveLength(many.length - 1);
  });

  test("test_a_press_shows_the_rest_under_itself_and_a_second_puts_them_away_and_the_press_is_of_one_size", async () => {
    const user = userEvent.setup({ delay: null });
    render(<Strip marks={[]} tags={meta.tags} asked={many} fold={FOLD} of={OF} />);
    const button = press();

    await user.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("list", { name: STRIP.restOf(OF) })).toHaveAttribute("data-folded", "false");
    expect(button).toHaveAccessibleName(CARD.moreOf(CARD.fewer, OF));
    // The press is where it was: what it shows stands under it, and what stood over it stands there still.
    expect(press()).toBe(button);
    expect([...holds().children].map((part) => part.tagName)).toEqual(["UL", "P", "UL"]);
    expect(shown()).toHaveLength(3);
    // It holds the room of both of the things it says, and draws the one: so it is as wide
    // saying the one as the other, and nothing of it changes size under the press.
    const said = [...button.querySelectorAll<HTMLElement>("[data-said]")];
    expect(said.map((one) => [one.textContent, one.getAttribute("data-said"), one.getAttribute("aria-hidden")])).toEqual([
      [CARD.more(2), "false", "true"],
      [CARD.fewer, "true", null],
    ]);
    expect([at(".saying").get("grid-row"), at(".saying").get("grid-column"), at(".says").get("display")]).toEqual(["1", "1", "grid"]);
    expect(at('.saying[data-said="false"]').get("visibility")).toBe("hidden");

    await user.click(button);
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByRole("list", { name: STRIP.restOf(OF) })).toHaveAttribute("data-folded", "true");
    expect(document.activeElement).toBe(button);
  });

  test("test_only_a_result_as_narrow_as_a_phone_folds_its_lines_and_a_wider_one_draws_no_press", () => {
    // The press is drawn, and what it shows is put away, by the width of the result and
    // never of the screen: in the narrow column of a wide screen a result folds as on a phone.
    expect(at(".fold").get("display")).toBe("none");
    expect(at(".fold", NARROW).get("display")).toBe("block");
    expect(at('.lines[data-folded="true"]', NARROW).get("display")).toBe("none");
    expect(RULES.filter((rule) => /data-folded/.test(rule.selector)).map((rule) => [rule.under, rule.selector])).toEqual([
      [NARROW, '.lines[data-folded="true"]'],
    ]);
    // It stands on a rule of sand, as a line does, and is as high as a small button of the look.
    expect(at(".fold").get("border-block-start")).toBe(at(".item").get("border-block-start"));
    expect(at(".fold > button").get("min-height")).toBe("var(--target-min)");
    expect(heavier(weightOf(".fold > button"), weightOf(".press"))).toBe(true);
  });

  test("test_a_line_that_says_no_data_is_never_folded_so_that_what_an_area_lacks_is_in_sight_with_nothing_pressed", () => {
    // Seen on a phone: a result said under its fit that its area is listed lower for what
    // it lacks, and the line that names what it lacks stood behind the press.
    const last = [MEASURED, JOURNEY, ESTIMATED, BUDGET, UNKNOWN];
    const { unmount } = render(<Strip marks={[]} tags={meta.tags} asked={last} fold={FOLD} of={OF} />);
    const namesOf = (held: HTMLElement[]) => held.map((line) => line.textContent);

    expect(last.map((one) => one.known)).toEqual(["whole", "whole", "some", "whole", "none"]);
    // It stands over the press with the first of the rest, each in the order of the search.
    expect(namesOf(shown())).toEqual([MEASURED.name, `${JOURNEY.name}${JOURNEY.figure}${JOURNEY.side}`, `${UNKNOWN.name}${KNOWN.none}`]);
    expect(rest().map((line) => line.querySelector("[data-known]")?.getAttribute("data-known"))).toEqual(["some", "whole"]);
    expect(press()).toHaveAccessibleName(CARD.moreOf(CARD.more(2), OF));
    unmount();

    // So does a vibe that was asked for and could not be worked out, which stands after the vibes that could.
    const vibes = render(<Strip marks={first.strip.filter((one) => one.asked)} tags={meta.tags} unplaced={["leafy"]} asked={[MEASURED, JOURNEY, BUDGET, UNKNOWN]} fold={FOLD} of={OF} />);
    expect(shown().map((line) => line.querySelector("[class*='name']")?.textContent)).toEqual([tagOf("pace").label, tagOf("leafy").label, UNKNOWN.name]);
    expect(rest()).toHaveLength(3);
    vibes.unmount();

    // Where an area lacks more than the lines that stand over the press, every one of them stands there.
    const none: readonly Asked[] = [1, 2, 3, 4].map((at) => ({ ...UNKNOWN, key: `journey ${at}` }));
    render(<Strip marks={[]} tags={meta.tags} asked={[MEASURED, ...none, BUDGET]} fold={FOLD} of={OF} />);
    expect(shown().map((line) => line.querySelector("[data-known]")?.getAttribute("data-known"))).toEqual(["none", "none", "none", "none"]);
    expect(rest()).toHaveLength(2);
  });

  test("test_a_line_counts_for_half_a_row_more_for_each_line_more_that_its_name_takes_so_that_long_names_fold_sooner", () => {
    // Measured at 390 by 844: the column of names has the room of sixteen letters on a
    // line, and a line is 38 px high, 46 where its name takes two lines and 66 where it
    // takes three. A long name takes room over the result as well, in its chip. After
    // "leafy and low crime" a result held three lines, two of them of measures whose names
    // take two lines and three: it showed them all, as a result of three lines does, and
    // ended 17 px under the foot of the first screen.
    const byLength = [...meta.features].sort((one, other) => other.short_label.length - one.short_label.length);
    const ofLines = (lines: number) => byLength.filter((metric) => Math.ceil(metric.short_label.length / 16) === lines);
    const [three, two, one] = [ofLines(3), ofLines(2), ofLines(1)];
    const lineOf = (metric: (typeof byLength)[number] | undefined): Asked => {
      if (metric === undefined) throw new Error("The recorded release holds no measure of such a name.");
      return { key: `measure ${metric.feature_id}`, name: metric.short_label, thing: { kind: "feature", id: metric.feature_id, family: metric.family }, known: "whole" };
    };
    const LETTERS = { ...FOLD, letters: 16 };
    const drawn = (lines: readonly Asked[]) => render(<Strip marks={[]} tags={meta.tags} asked={lines} fold={LETTERS} of={OF} />);
    const names = (held: HTMLElement[]) => held.map((line) => line.textContent);

    expect([three.length > 1, two.length > 1, one.length > 3]).toEqual([true, true, true]);
    // Names of one line, two and three: a row, a row and a half, and two. Four and a half rows, where four have room.
    const tight = [lineOf(one[0]), lineOf(two[0]), lineOf(three[0])];
    const folded = drawn(tight);
    expect(names(shown())).toEqual(tight.slice(0, 2).map((line) => line.name));
    expect(names(rest())).toEqual(tight.slice(2).map((line) => line.name));
    expect(press()).toHaveAccessibleName(CARD.moreOf(CARD.more(1), OF));
    folded.unmount();
    // Two lines of long names are three rows and a half, and both stand.
    const both = drawn([lineOf(two[0]), lineOf(three[0])]);
    expect([shown().length, screen.queryAllByRole("button").length]).toEqual([2, 0]);
    both.unmount();
    // Four lines of short names have the room of four rows, and none is folded.
    const four = drawn(one.slice(0, 4).map(lineOf));
    expect([shown().length, screen.queryAllByRole("button").length]).toEqual([4, 0]);
    four.unmount();
    // A line is never left out for the length of its name alone: the first stands, however long.
    const long = { ...lineOf(three[0]), name: [three[0], three[1], two[0]].map((metric) => metric?.short_label).join(" ") };
    const alone = drawn([long, lineOf(three[1]), lineOf(one[0])]);
    expect(Math.ceil(long.name.length / 16)).toBeGreaterThan(5);
    expect(names(shown())).toEqual([long.name]);
    expect(rest()).toHaveLength(2);
    alone.unmount();
    // Told of no letters, every line counts for one row.
    render(<Strip marks={[]} tags={meta.tags} asked={tight} fold={FOLD} of={OF} />);
    expect([shown().length, screen.queryAllByRole("button").length]).toEqual([3, 0]);
  });

  test("test_the_vibes_nobody_asked_for_are_never_folded", () => {
    render(<Strip marks={first.strip} tags={meta.tags} asked={many} fold={FOLD} of={OF} />);
    const others = within(screen.getByRole("list", { name: STRIP.othersOf(OF) })).getAllByRole("listitem");

    expect(others).toHaveLength(first.strip.filter((one) => !one.asked).length);
    expect(others.length).toBeGreaterThan(0);
    expect(screen.getByRole("list", { name: STRIP.othersOf(OF) })).not.toHaveAttribute("data-folded");
    expect([...holds().children].map((part) => part.tagName)).toEqual(["UL", "P", "UL", "UL"]);
  });
});

describe("each list says what it holds", () => {
  test("test_a_list_is_named_for_what_was_asked_for_or_for_the_vibes_that_were_not", () => {
    const [asked, others] = [first.strip.filter((one) => one.asked), first.strip.filter((one) => !one.asked)];
    expect([asked.length > 0, others.length > 0]).toEqual([true, true]);

    // What was asked for, of the area. It was named "Vibes of" the area whatever it held.
    const wanted = render(<Strip marks={asked} tags={meta.tags} asked={[JOURNEY]} of={OF} />);
    expect(screen.getAllByRole("list").map((list) => list.getAttribute("aria-label"))).toEqual([STRIP.askedOf(OF)]);
    wanted.unmount();
    // The vibes of the area, where nothing was asked for.
    const none = render(<Strip marks={others} tags={meta.tags} of={OF} />);
    expect(screen.getAllByRole("list").map((list) => list.getAttribute("aria-label"))).toEqual([STRIP.label(OF)]);
    none.unmount();
    // Both, where the look has the vibes nobody asked for stand under what was.
    render(<Strip marks={first.strip} tags={meta.tags} asked={[JOURNEY]} of={OF} />);
    expect(screen.getAllByRole("list").map((list) => list.getAttribute("aria-label"))).toEqual([STRIP.askedOf(OF), STRIP.othersOf(OF)]);
    expect([STRIP.askedOf(OF), STRIP.restOf(OF), STRIP.label(OF), STRIP.othersOf(OF)]).toEqual([
      `What you asked for in ${OF}`,
      `More of what you asked for in ${OF}`,
      `Vibes of ${OF}`,
      `Other vibes of ${OF}`,
    ]);
  });
});

describe("the steps of every line stand in one column", () => {
  // The founder, who had walked the website twice: "on the ranking cards, ensure the gauges
  // all line up vertically so that a user can scan downwards with ease". Measured in a
  // browser at 1440 by 900, the steps of the first three results began at 411.78, 403.8,
  // 464.22, 248.66, 399.16, 394.86 and 281.66 px: wherever the name before them ended. No
  // page is laid out here, so what is held is what lays a line out.
  const named = (tagId: string) => meta.tags.find((tag) => tag.tag_id === tagId)?.label ?? "";

  test("test_a_line_is_three_columns_and_the_gauge_begins_where_the_column_of_names_ends", () => {
    const { container } = render(<Strip marks={first.strip} tags={meta.tags} facts={facts} of={OF} />);

    // The name, the gauge, and the rest: the first as wide as what stands in it, up to the
    // most it is given, the second as wide as the gauge, and the third with what is left.
    expect(at(".mark").get("display")).toBe("grid");
    expect(at(".mark").get("grid-template-columns")).toBe("fit-content(var(--names-most)) auto minmax(0, 1fr)");
    expect([at(".first").get("grid-row"), at(".first").get("grid-column")]).toEqual(["1 / span 2", "1"]);
    expect([at(".picture").get("grid-row"), at(".picture").get("grid-column")]).toEqual(["1 / span 2", "2"]);
    // At no width a phone gives a result is a line laid out in other columns, and at none
    // do the name or the gauge leave theirs. Under it a line has not the room of the two.
    const columns = RULES.filter((rule) => /\.mark(\[[^\]]*\])*$/.test(rule.selector) && rule.sets.has("grid-template-columns"));
    expect(columns.map((rule) => rule.under)).toEqual([null, NO_ROOM]);
    const moved = RULES.filter(
      (rule) => /\.(first|picture)(\[[^\]]*\])*$/.test(rule.selector) && ["grid-column", "order"].some((property) => rule.sets.has(property)),
    );
    expect(moved.map((rule) => [rule.under, rule.selector])).toEqual([
      [null, ".first"],
      [null, ".picture"],
      [NO_ROOM, ".mark > .picture"],
    ]);
    const [line] = container.querySelectorAll<HTMLElement>("li > span");
    for (let rem = AT_360; rem <= 60; rem += 0.5) {
      const [ofTheLine, ofTheGauge] = [line, line?.querySelector(".picture")].map((part) => setAt(RULES, part as HTMLElement, rem));
      expect([rem, ofTheLine?.get("grid-template-columns"), ofTheGauge?.get("grid-column")]).toEqual([
        rem,
        "fit-content(var(--names-most)) auto minmax(0, 1fr)",
        "2",
      ]);
    }
    // Every line is made of the same parts, in the same order, whatever its vibe.
    for (const line of container.querySelectorAll("li")) {
      const whole = line.firstElementChild?.getAttribute("data-known") === "whole";
      // After the gauge of a band that is not whole stand the two words that say so, and nothing after any other.
      expect([...(line.firstElementChild as HTMLElement).children].map((part) => part.className.split(" ")[0])).toEqual(
        whole ? ["first", "picture"] : ["first", "picture", "approx"],
      );
      expect([...(line.querySelector(".first") as HTMLElement).children].map((part) => part.className)).toEqual(["title", "wide"]);
      expect([...(line.querySelector(".title") as HTMLElement).children].map((part) => part.className)).toEqual(["thing", "titled"]);
    }
  });

  test("test_the_room_of_an_end_is_of_one_width_on_every_line_so_that_the_steps_begin_in_one_place", () => {
    // Before the steps stands the picture of the low end, which is as wide whatever it is of.
    expect(at(".strip").get("--room")).toBe("calc(var(--px-ground) * 16)");
    expect(at(".picture").get("grid-template-columns")).toBe("var(--room) auto var(--room)");
    expect(at(".picture").get("gap")).toBe("var(--px-ground) var(--beside)");
    expect(at(".picture > :not(.end)").get("grid-column")).toBe("2");
    expect([at(".end > *").get("grid-column"), at(".end ~ .end > *").get("grid-column")]).toEqual(["1", "3"]);
    // An end is no box of its own: its picture is laid out by the gauge, on the line the steps stand on.
    expect(at(".end").get("display")).toBe("contents");
    expect(at(".picture").get("align-items")).toBe("end");
    // The name of an end is laid under the gauge and is no part of its line, so it moves no step.
    expect(at(".picture > .named").get("grid-row")).toBe("2");
    // At no width is the room of an end, or where a gauge is laid out, another.
    const again = RULES.filter(
      (rule) => rule.under !== null && (rule.sets.has("--room") || (/\.picture/.test(rule.selector) && rule.sets.has("grid-template-columns"))),
    );
    expect(again).toEqual([]);
    // Before the name stands the drawing of the thing, in a room of one width.
    expect(at(".strip").get("--marker")).toBe("calc(var(--px-ground) * 18)");
    expect(at(".title").get("grid-template-columns")).toBe("var(--marker) minmax(0, 1fr)");
  });

  test("test_the_column_of_names_is_as_wide_as_the_longest_name_that_stands_in_it", () => {
    // A style sheet cannot be told how wide a name is. It is told the names, and lays them
    // in the column of every line, where none is drawn: the column is then as wide in one
    // line as in the next.
    const { unmount } = render(<Strip marks={first.strip} tags={meta.tags} unplaced={["leafy"]} asked={[JOURNEY, BUDGET]} of={OF} />);
    const own = first.strip.map((mark) => named(mark.tag_id));
    const [asked, others] = [true, false].map((kept) => first.strip.filter((mark) => mark.asked === kept).map((mark) => named(mark.tag_id)));
    const held = holds;

    expect(own.length).toBeGreaterThan(2);
    // Of the lines it draws, in the order they stand in: the vibes that were asked for, the
    // vibe it could not work out, what else was asked for, and the vibes that were not.
    expect(held().style.getPropertyValue("--names")).toBe(asLines([...(asked ?? []), named("leafy"), JOURNEY.name, BUDGET.name, ...(others ?? [])]));
    expect(held().style.getPropertyValue("--groups")).toBe(asLines([STRIP.group.asked, STRIP.group.also]));
    unmount();
    // A list of results has a column of one width from one result to the next: it hands
    // every strip the names of all of them.
    const all = namesOf(calm.ranked.map((area) => area.strip), meta.tags);
    render(<Strip marks={first.strip} tags={meta.tags} of={OF} names={all} />);
    expect(all.length).toBeGreaterThan(own.length);
    expect(held().style.getPropertyValue("--names")).toBe(asLines(all));

    // They are laid in the column as a name is set, as far in as a name stands.
    expect(at(".wide::before").get("content")).toBe('var(--names, "")');
    expect(at(".wide::before").get("font")).toBe(at(".name").get("font"));
    expect(at(".wide::before").get("padding-inline-start")).toBe("var(--marker)");
    expect(at(".wide::after").get("content")).toBe('var(--groups, "")');
    expect(at(".wide::after").get("font")).toBe(
      `400 ${at(".group").get("font-size")} / ${at(".group").get("line-height")} var(--font-say)`,
    );
    // What holds them asks of the line the width of the widest of them.
    expect(at(".first").get("display")).toBe("block");
    expect(at(".wide").get("display")).toBe("block");
    expect([at(".first").get("min-width"), at(".first").get("width"), at(".first").get("overflow")]).toEqual([undefined, undefined, undefined]);
  });

  test("test_what_is_said_of_asking_is_laid_in_the_column_only_where_a_line_says_it", () => {
    const asked = first.strip.filter((mark) => mark.asked);
    render(<Strip marks={asked} tags={meta.tags} of={OF} />);

    expect(asked.length).toBeGreaterThan(0);
    expect(holds().style.getPropertyValue("--groups")).toBe(asLines([]));
  });

  test("test_the_two_words_that_may_stand_under_a_name_are_laid_in_the_column_of_every_line_so_that_no_line_is_wider_for_them", () => {
    // Measured on a phone: a line that said "approx data" under its name had a wider column
    // than the line over it, and its steps began 13 px further along.
    render(<Strip marks={first.strip} tags={meta.tags} of={OF} />);
    const held = holds();
    const APPROX = rulesOf(readFileSync(path.join(__dirname, "../kit/Approx/Approx.module.css"), "utf8"));
    const ofTheWords = (selector: string) => new Map(APPROX.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

    expect(UNDER_A_NAME).toEqual([
      { says: KNOWN.some, more: BEFORE_THE_TWO_WORDS },
      { says: KNOWN.none, more: BEFORE_THE_TWO_WORDS },
    ]);
    expect([held.style.getPropertyValue("--beside-1"), held.style.getPropertyValue("--beside-2")]).toEqual([asLines([KNOWN.some]), asLines([KNOWN.none])]);
    expect([held.style.getPropertyValue("--beside-1-more"), held.style.getPropertyValue("--beside-2-more")]).toEqual(["11", "11"]);
    // The room before the words is the mark, which is as wide as a step of a band, and the
    // room between the mark and the words, as the part that draws them lays them.
    expect(sizeOf("ui-approx").width).toBe(9);
    expect(ofTheWords(".approx").get("gap")).toBe("calc(var(--px) * 2)");
    expect(ofTheWords(".blank").get("width")).toBe("calc(var(--px) * 9)");
    expect(BEFORE_THE_TWO_WORDS).toBe(9 + 2);
    // Both are drawn at the pixel of the ground there, and are laid in the column by it.
    expect(at(".said").get("--px")).toBe("var(--px-ground)");
    for (const [laid, nth] of [[".first::before", 1], [".first::after", 2]] as const) {
      expect([laid, at(laid).get("content")]).toEqual([laid, `var(--beside-${nth}, "")`]);
      expect([laid, at(laid).get("padding-inline-start")]).toEqual([laid, `calc(var(--marker) + var(--px-ground) * var(--beside-${nth}-more, 0))`]);
      // They are set as they are read, and are never broken: the column is never narrower than they are.
      expect([laid, at(laid).get("font"), at(laid).get("white-space")]).toEqual([laid, ofTheWords(".said").get("font"), "pre"]);
      expect([laid, at(laid).get("height"), at(laid).get("visibility"), at(laid).get("overflow")]).toEqual([laid, "0", "hidden", "clip"]);
    }
    // Under a name they stand as far in as the name does.
    expect(at(".said").get("padding-inline-start")).toBe("var(--marker)");
  });

  test("test_what_is_laid_in_the_column_is_not_drawn_takes_no_height_and_is_no_word_of_the_page", () => {
    const { container } = render(<Strip marks={first.strip} tags={meta.tags} facts={facts} of={OF} />);

    for (const laid of [".wide::before", ".wide::after"]) {
      expect([laid, at(laid).get("height"), at(laid).get("visibility"), at(laid).get("overflow")]).toEqual([laid, "0", "hidden", "clip"]);
    }
    // What holds them holds no word, and is kept from whoever hears the page.
    const holds = [...container.querySelectorAll(".wide")];
    expect(holds).toHaveLength(first.strip.length);
    for (const one of holds) {
      expect([one.textContent, one.childElementCount, one.getAttribute("aria-hidden")]).toEqual(["", 0, "true"]);
    }
    // So the name of a vibe is written once, in the line of that vibe, and in no other.
    for (const mark of first.strip) expect(screen.getAllByText(named(mark.tag_id))).toHaveLength(1);
  });

  test("test_a_name_longer_than_the_column_breaks_onto_a_second_line_and_none_is_cut", () => {
    // The most the column is given, the drawing before a name with it: under half of the
    // result, no less than 8rem and no more than 14rem.
    expect(at(".strip").get("--names-most")).toBe("clamp(8rem, 45cqi, 14rem)");
    expect(at(".name").get("overflow-wrap")).toBe("break-word");
    // The names that are laid in the column break as a name does, so they ask for no more
    // than the column can be given.
    expect(at(".wide::before").get("white-space")).toBe("pre-line");
    // Nothing cuts a name short, hides what runs over, or keeps it on one line.
    const cuts = RULES.filter(
      (rule) =>
        /\.(name|title|titled|first|mark)$/.test(rule.selector) &&
        (rule.sets.has("text-overflow") || rule.sets.has("overflow") || rule.sets.get("white-space") === "nowrap" || rule.sets.has("max-height")),
    );
    expect(cuts.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_two_words_stand_after_the_gauge_where_a_result_has_the_room_and_under_the_name_where_it_has_not", () => {
    // Measured on a phone: after the name, the gauge and its two pictures a line has some
    // 50 px left, and the two words need twice that.
    expect([at(".said").get("grid-row"), at(".said").get("grid-column"), at(".said").get("padding-inline-start")]).toEqual([
      "2",
      "1",
      "var(--marker)",
    ]);
    expect(at('.mark[data-known="some"] > .first').get("grid-row")).toBe("1");
    expect(at('.mark[data-known="none"] > .first').get("grid-row")).toBe("1");
    // After a gauge, and after a figure, which stands where a gauge stands.
    const after = at(".mark[data-known]:has(> .picture, > .told) > .said", WIDE);
    expect([after.get("grid-row"), after.get("grid-column"), after.get("padding-inline-start")]).toEqual(["1 / span 2", "3", "0"]);
    expect(at(".mark[data-known] > .first", WIDE).get("grid-row")).toBe("1 / span 2");
    // A line with neither says them where a gauge begins, at every width.
    const alone = at(".mark:not(:has(> .picture, > .told)) > .said");
    expect([alone.get("grid-row"), alone.get("grid-column")]).toEqual(["1 / span 2", "2 / -1"]);
    // The gauge stands beside the name and the two words, and is never moved for them: it
    // has a line of its own only where a result has not the room of a name and a gauge.
    const moved = RULES.filter((rule) => /\.picture(\[[^\]]*\])*$/.test(rule.selector) && rule.sets.has("grid-row"));
    expect(moved.map((rule) => [rule.under, rule.selector])).toEqual([
      [null, ".picture"],
      [NO_ROOM, ".mark > .picture"],
    ]);
  });

  test("test_in_a_result_narrower_than_a_phone_gives_the_gauge_has_the_line_under_the_name_and_nothing_runs_past_the_result", () => {
    // Seen in a browser, in a window 320 px wide: the column of names is never narrower
    // than the two words that may stand under a name, 141 px with the room of their mark,
    // and a gauge is 154 px with its two pictures. Side by side the two wanted 303 px of a
    // line of 268: the gauge ran 35 px past its result, its far picture was cut by the edge
    // of the box, and the page scrolled sideways.
    const { container } = render(
      <Strip marks={first.strip} tags={meta.tags} facts={withFact(first.strip[0]?.fact_id ?? "", { known: "2", parts: "3" })} of={OF} asked={EVERY_KIND} />,
    );
    const marks = [...container.querySelectorAll<HTMLElement>("li > span")];
    const withAGauge = marks.filter((mark) => mark.querySelector(".picture") !== null);
    const notWhole = withAGauge.find((mark) => mark.dataset.known === "some") as HTMLElement;
    const withAFigure = marks.filter((mark) => mark.querySelector(".told") !== null);
    const withNone = marks.find((mark) => mark.querySelector(".picture, .told") === null) as HTMLElement;
    expect([withAGauge.length > 1, notWhole !== undefined, withAFigure.length, withNone.dataset.known]).toEqual([true, true, 3, "none"]);

    for (let rem = 12; rem <= 21; rem += 0.5) {
      for (const mark of marks) {
        const of = (part: string) => setAt(RULES, mark.querySelector(part) as HTMLElement, rem);
        // One column, which is never wider than the line: what stands in it breaks, and pushes nothing out.
        expect([rem, setAt(RULES, mark, rem).get("grid-template-columns")]).toEqual([rem, "minmax(0, 1fr)"]);
        expect([rem, rowOf(of(".first")), of(".first").get("grid-column")]).toEqual([rem, 1, "1"]);
        if (mark.querySelector(".picture") !== null) {
          // The gauge under the name, as far in as the name stands.
          expect([rem, rowOf(of(".picture")), of(".picture").get("grid-column")]).toEqual([rem, 2, "1"]);
          expect([rem, of(".picture").get("justify-self"), of(".picture").get("margin-inline-start")]).toEqual([rem, "start", "var(--marker)"]);
        }
        if (mark.querySelector(".told") !== null) {
          // A figure under the name, as a gauge is, and as far in.
          expect([rem, rowOf(of(".told")), of(".told").get("grid-column")]).toEqual([rem, 2, "1"]);
          expect([rem, of(".told").get("justify-self"), of(".told").get("margin-inline-start")]).toEqual([rem, "start", "var(--marker)"]);
        }
        if (mark.dataset.known !== "whole") {
          // The two words under both, as far in: of a line that has a gauge, and of one that has none.
          const said = setAt(RULES, mark.querySelector("[class~='said']") as HTMLElement, rem);
          expect([rem, rowOf(said), said.get("grid-column"), said.get("padding-inline-start")]).toEqual([rem, 3, "1", "var(--marker)"]);
        }
      }
    }
    // A result in a window 320 px wide is one, and one in the narrowest phone that is common is not.
    const columnsAt = (rem: number) => setAt(RULES, marks[0] as HTMLElement, rem).get("grid-template-columns");
    expect([columnsAt(AT_320), columnsAt(AT_360)]).toEqual(["minmax(0, 1fr)", "fit-content(var(--names-most)) auto minmax(0, 1fr)"]);
    // The steps of every line begin in one place there too: each gauge begins where its line begins.
    expect(at(".mark > .picture", NO_ROOM).get("grid-column")).toBe("1");
  });

  test("test_a_short_line_keeps_the_columns_of_every_line_and_a_narrow_result_has_narrower_steps", () => {
    const TRACK = rulesOf(readFileSync(path.join(__dirname, "../Track/Track.module.css"), "utf8"));
    const track = new Map(TRACK.filter((rule) => rule.selector === ".track" && rule.under === null).flatMap((rule) => [...rule.sets]));

    // A line of steps is five steps, an art pixel between each two and one at either side.
    expect([track.get("grid-template-columns"), track.get("gap"), track.get("padding")]).toEqual([
      "repeat(5, calc(var(--px) * var(--step)))",
      "var(--px)",
      "calc(var(--px) * var(--room)) var(--px) 0",
    ]);
    expect(track.get("--step")).toBe("var(--track-step, 9)");
    // On a result as narrow as a phone the steps are narrower, in every line, and a line
    // keeps one art pixel over it and under it where it keeps two.
    expect(at(".picture", NARROW).get("--track-step")).toBe("7");
    expect([at(".item").get("padding-block"), at(".item", NARROW).get("padding-block")]).toEqual(["calc(var(--px) * 2)", "var(--px)"]);
    const said = RULES.filter((rule) => rule.sets.has("--track-step"));
    expect(said.map((rule) => [rule.under, rule.selector])).toEqual([[NARROW, ".picture"]]);

    const { container } = render(<Strip marks={first.strip} tags={meta.tags} of={OF} short />);
    for (const line of container.querySelectorAll("li")) {
      expect([...(line.firstElementChild as HTMLElement).children].map((part) => part.className.split(" ")[0])).toEqual(["first", "picture"]);
    }
    expect(at('.strip[data-short="true"] .item').get("border-block-start")).toBe("0");
  });

  test("test_a_strip_is_laid_out_by_the_width_of_the_result_that_holds_it_and_never_of_the_screen", () => {
    const conditions = [...new Set(RULES.map((rule) => rule.under).filter((under) => under?.startsWith("@container")))];

    expect(RULES.filter((rule) => rule.sets.has("container-type") || rule.sets.has("container")).map((rule) => rule.selector)).toEqual([]);
    expect(conditions).toEqual([NARROW, NO_ROOM, WIDE]);
    // What every line is given is said of the strip, once, so that no line can be given another.
    for (const name of ["--marker", "--names-most", "--room", "--beside"]) {
      expect([name, RULES.filter((rule) => rule.sets.has(name)).map((rule) => [rule.under, rule.selector])]).toEqual([name, [[null, ".strip"]]]);
    }
    expect(RULES.filter((rule) => rule.sets.has("--between")).map((rule) => [rule.under, rule.selector, rule.sets.get("--between")])).toEqual([
      [null, ".strip", "var(--space-2)"],
      [WIDE, ".strip", "var(--space-3)"],
    ]);
  });
});

describe("the gauge, as a part of its own", () => {
  test("test_it_is_one_picture_whose_name_says_the_band_and_both_ends", () => {
    const scale = tagOf("pace");
    const { container } = render(
      <p>
        <Picture mark={markOf("pace")} tag={scale} />
      </p>,
    );
    const picture = screen.getByRole("img");

    expect(container.textContent).toBe("");
    expect(picture).toHaveAccessibleName(
      `${STRIP.band(markOf("pace").band)}, ${STRIP.from("Calm", "Buzzy")}, ${STRIP.askedFor("Calm")}`,
    );
    expect([picture.className, picture.getAttribute("data-as"), picture.getAttribute("data-ends"), picture.childElementCount]).toEqual([
      "picture",
      "line",
      "pictured",
      3,
    ]);
    expect(container.querySelectorAll("[role='img']")).toHaveLength(1);
  });
});
