import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { BAND_ON_A_SCALE, BAND_ONE_WAY, BAND_VARIES, RESTS_ON } from "@/content/bands";
import { CARD } from "@/content/card";
import { KNOWN, PEG } from "@/content/kit";
import { STRIP } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Fact, StripMark, Tag } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { rowOf, setAt } from "../../../test/support/cascade";
import { rulesOf } from "../../../test/support/css";
import { figuresNotFrom } from "../../../test/support/figures";
import { ROUGH } from "../../../test/support/rough";
import { endsOf, inWords } from "@/lib/vibes";

import { sizeOf } from "../kit/drawings";
import { picturesAtEnds } from "../kit/Ends/picture";
import { drawingOf } from "../kit/Thing/drawn";
import { asLines, namesOf } from "./column";
import { BEFORE_THE_TWO_WORDS, isFromPart, Picture, Strip, UNDER_A_NAME } from "./Strip";

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
/** The lines of the vibes of a strip. */
const lines = (of: string = OF) => within(screen.getByRole("list", { name: STRIP.label(of) })).getAllByRole("listitem");
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
    expect(RULES.filter((rule) => rule.sets.get("display") === "none").map((rule) => rule.selector)).toEqual([]);
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
        lacked={[{ name: "Journey", thing: { kind: "place" } }]}
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
    expect(screen.getByRole("list").parentElement).toHaveAttribute("data-ends", "pictured");
    expect(document.querySelectorAll("[class*='ofEnd'], [class*='named']")).toHaveLength(0);
    unmount();
    render(<Strip marks={first.strip} tags={meta.tags} of={OF} ends="named" />);
    const marks = lines();

    expect(screen.getByRole("list").parentElement).toHaveAttribute("data-ends", "named");
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
    expect(screen.getByRole("list").parentElement).toHaveAttribute("data-short", "true");
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

  test("test_what_else_was_asked_for_and_has_no_figure_is_named_in_a_list_of_its_own_and_said_to_be_not_known", () => {
    const { container } = render(
      <Strip
        marks={[mark]}
        tags={meta.tags}
        lacked={[
          { name: "Journey", thing: { kind: "place" } },
          { name: "Budget", thing: { kind: "budget" } },
        ]}
        of={OF}
      />,
    );
    const lacked = within(screen.getByRole("list", { name: CARD.lacked(OF) })).getAllByRole("listitem");

    // It is no vibe, and stands in no list of vibes.
    expect(lines()).toHaveLength(1);
    expect(lacked.map((line) => line.textContent)).toEqual([`Journey${KNOWN.none}`, `Budget${KNOWN.none}`]);
    // It has the drawing of its kind before its name, and no gauge: nothing is drawn of a
    // figure that is not known.
    expect(lacked.map((line) => line.querySelector<HTMLElement>("[class*='title'] [aria-hidden='true'] > span")?.style.getPropertyValue("--art"))).toEqual([
      served(drawingOf({ kind: "place" })),
      served(drawingOf({ kind: "budget" })),
    ]);
    for (const line of lacked) {
      expect(line.querySelector("[role='img'], [class*='track']")).toBeNull();
      expect(line.firstElementChild).toHaveAttribute("data-known", "none");
    }
    expect(container.querySelectorAll("button, a")).toHaveLength(0);
    // With nothing else to draw, the list stands alone.
    render(<Strip marks={[]} tags={meta.tags} lacked={[{ name: "Journey", thing: { kind: "place" } }]} of="Elsewhere" />);
    expect(screen.queryByRole("list", { name: STRIP.label("Elsewhere") })).toBeNull();
    expect(screen.getByRole("list", { name: CARD.lacked("Elsewhere") })).toBeInTheDocument();
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
    const { unmount } = render(
      <Strip marks={first.strip} tags={meta.tags} unplaced={["leafy"]} lacked={[{ name: "Journey", thing: { kind: "place" } }]} of={OF} />,
    );
    const own = first.strip.map((mark) => named(mark.tag_id));
    const held = () => screen.getAllByRole("list")[0]?.parentElement as HTMLElement;

    expect(own.length).toBeGreaterThan(2);
    // Of the vibes it draws, of the vibe it could not work out, and of what else it names.
    expect(held().style.getPropertyValue("--names")).toBe(asLines([...own, named("leafy"), "Journey"]));
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
    expect(screen.getByRole("list").parentElement?.style.getPropertyValue("--groups")).toBe(asLines([]));
  });

  test("test_the_two_words_that_may_stand_under_a_name_are_laid_in_the_column_of_every_line_so_that_no_line_is_wider_for_them", () => {
    // Measured on a phone: a line that said "approx data" under its name had a wider column
    // than the line over it, and its steps began 13 px further along.
    render(<Strip marks={first.strip} tags={meta.tags} of={OF} />);
    const held = screen.getByRole("list").parentElement as HTMLElement;
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
    const after = at(".mark[data-known]:has(> .picture) > .said", WIDE);
    expect([after.get("grid-row"), after.get("grid-column"), after.get("padding-inline-start")]).toEqual(["1 / span 2", "3", "0"]);
    expect(at(".mark[data-known] > .first", WIDE).get("grid-row")).toBe("1 / span 2");
    // A line with no gauge says them where a gauge begins, at every width.
    const alone = at(".mark:not(:has(> .picture)) > .said");
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
    const lacking = [{ name: "Budget", thing: { kind: "budget" } as const }];
    const { container } = render(
      <Strip marks={first.strip} tags={meta.tags} facts={withFact(first.strip[0]?.fact_id ?? "", { known: "2", parts: "3" })} of={OF} lacked={lacking} />,
    );
    const marks = [...container.querySelectorAll<HTMLElement>("li > span")];
    const withAGauge = marks.filter((mark) => mark.querySelector(".picture") !== null);
    const notWhole = withAGauge.find((mark) => mark.dataset.known === "some") as HTMLElement;
    const withNone = marks.find((mark) => mark.querySelector(".picture") === null) as HTMLElement;
    expect([withAGauge.length > 1, notWhole !== undefined, withNone.dataset.known]).toEqual([true, true, "none"]);

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
