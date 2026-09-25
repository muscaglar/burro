import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { STRIP } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Fact, StripMark } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { figuresNotFrom, saidBy } from "../../../test/support/figures";
import { endsOf, inWords } from "@/lib/vibes";

import { RoughOnResult, Strip } from "./Strip";

const meta = recordedAnswer("get_meta", "meta").body.data;
const calm = recordedAnswer("rank", "rank-scale").body.data;
const reasons = recordedAnswer("explain_top", "explanations-scale").body.data;
const facts: Record<string, Fact> = Object.fromEntries(reasons.facts.map((fact) => [fact.fact_id, fact]));

const first = calm.ranked[0];
if (first === undefined) throw new Error("The recording holds no result.");

/** The result whose strip holds a mark drawn as a range. */
const mixed = calm.ranked.find((area) => area.strip.some((mark) => mark.spread_high - mark.spread_low >= 2));
if (mixed === undefined) throw new Error("The recording holds no mixed area.");

const markOf = (tagId: string, marks: readonly StripMark[] = first.strip) =>
  marks.find((mark) => mark.tag_id === tagId) as StripMark;
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

describe("a vibe that is a rough guide, on a result", () => {
  const asked = recordedAnswer("rank", "rank-rough-guide").body.data;
  const [top] = asked.ranked;
  if (top === undefined) throw new Error("The recording holds no result.");
  const [told] = meta.rough_guides;

  test("test_it_is_on_a_result_only_where_it_was_asked_for", () => {
    for (const area of asked.ranked) {
      for (const mark of area.strip.filter((one) => one.tag_id === "village_feel")) expect(mark.asked).toBe(true);
    }
    expect(top.strip.map((mark) => mark.tag_id)).toContain("village_feel");
    // Asked for nothing of the kind, no result of any search shows it.
    for (const area of calm.ranked) expect(area.strip.map((mark) => mark.tag_id)).not.toContain("village_feel");
  });

  test("test_its_mark_bears_its_label_after_its_name_and_no_other_mark_does", () => {
    render(<Strip marks={top.strip} tags={meta.tags} guides={meta.rough_guides} of="Wickerford" />);
    const marks = within(screen.getByRole("list", { name: STRIP.label("Wickerford") })).getAllByRole("listitem");

    const labelled = marks.filter((mark) => mark.querySelector("[data-rough-guide='label']") !== null);
    expect(labelled).toHaveLength(1);
    expect(heardIn(labelled[0])).toContain(`Village feel, ${told?.label}`);
    // The word is drawn, and is not kept for a screen reader alone.
    const label = labelled[0]?.querySelector("[data-rough-guide='label']");
    expect(label?.closest("[aria-hidden='true']")).toBeNull();
    expect(label?.lastChild?.textContent).toBe(told?.label);
  });

  test("test_the_sentence_that_says_why_stands_under_the_strip_in_sight_once_for_the_vibe", () => {
    const { container } = render(
      <RoughOnResult marks={top.strip} tags={meta.tags} guides={meta.rough_guides} />,
    );

    const notes = [...container.querySelectorAll("[data-rough-guide='note']")];
    expect(notes.map((note) => note.textContent)).toEqual([`Village feel: ${told?.label}. ${told?.why}`]);
    expect(container.querySelector("details, button, [hidden]")).toBeNull();
  });

  test("test_nothing_is_said_of_a_result_that_shows_no_such_vibe_or_where_the_api_says_nothing", () => {
    const { container } = render(
      <>
        <RoughOnResult marks={first.strip} tags={meta.tags} guides={meta.rough_guides} />
        <RoughOnResult marks={top.strip} tags={meta.tags} />
        <Strip marks={top.strip} tags={meta.tags} of="Wickerford" />
      </>,
    );

    expect(container.querySelector("[data-rough-guide]")).toBeNull();
  });
});

describe("the strip of vibes under a result's name", () => {
  test("test_each_mark_is_named_by_the_api_and_says_its_band_in_words", () => {
    render(<Strip marks={first.strip} tags={meta.tags} of="Alderwick" />);
    const marks = within(screen.getByRole("list", { name: STRIP.label("Alderwick") })).getAllByRole("listitem");

    expect(marks).toHaveLength(first.strip.length);
    first.strip.forEach((mark, at) => {
      const label = meta.tags.find((tag) => tag.tag_id === mark.tag_id)?.label ?? "";
      expect(marks[at]).toHaveTextContent(label);
      expect(pictureIn(marks[at])).toContain(STRIP.band(mark.band));
    });
  });

  test("test_the_picture_of_a_mark_says_what_it_shows_and_nothing_is_kept_for_a_screen_reader_alone", () => {
    const { container } = render(<Strip marks={first.strip} tags={meta.tags} of="Alderwick" />);

    // The band is drawn, and the drawing is named. It is not a sentence hidden from the eye.
    expect(container.querySelectorAll(".visually-hidden")).toHaveLength(0);
    // What is drawn for the eye alone is a word that the picture it stands beside says too:
    // that a mark was asked for, and the name of an end.
    for (const drawn of container.querySelectorAll("[aria-hidden='true']")) {
      const said = pictureIn(drawn.closest("li") as HTMLElement);
      const word = drawn.textContent ?? "";
      expect(word === STRIP.group.also || said.toLowerCase().includes(word.toLowerCase())).toBe(true);
    }
    expect(screen.getAllByRole("img")).toHaveLength(first.strip.length);
  });

  test("test_a_scale_names_both_its_ends_and_the_one_asked_for", () => {
    render(<Strip marks={first.strip} tags={meta.tags} of="Alderwick" />);
    const pace = screen.getAllByRole("listitem")[0] as HTMLElement;

    expect(markOf("pace")).toMatchObject({ asked: true, toward: "low" });
    expect(pace).toHaveTextContent("Calm");
    expect(pace).toHaveTextContent("Buzzy");
    // Which end was asked for is said in the name of the picture, and that end is drawn heavier.
    expect(pictureIn(pace)).toBe(
      `${STRIP.band(markOf("pace").band)}, ${STRIP.from("Calm", "Buzzy")}, ${STRIP.askedFor("Calm")}`,
    );
    expect([...pace.querySelectorAll("[data-asked='true']")].map((end) => end.textContent)).toContain("Calm");
    expect([...pace.querySelectorAll("[data-asked='false']")].map((end) => end.textContent)).toContain("Buzzy");
  });

  test("test_a_mark_is_heard_as_one_phrase_in_which_no_end_is_said_twice", () => {
    // Heard in a browser: "asked for: Buzzy Buzzy". The name of the end that was asked for
    // was said by the picture, and then again by the word drawn after it.
    const buzzy = recordedAnswer("rank", "rank-scale-turned").body.data.ranked[0]?.strip ?? [];
    render(<Strip marks={buzzy} tags={meta.tags} of="Pellam Cross" />);
    const pace = screen.getAllByRole("listitem")[0] as HTMLElement;

    expect(markOf("pace", buzzy)).toMatchObject({ asked: true, toward: "high", band: 5 });
    expect(heardIn(pace)).toBe(`Going out ${STRIP.band(5)}, ${STRIP.from("Calm", "Buzzy")}, ${STRIP.askedFor("Buzzy")}`);
    expect(heardIn(pace).split("Buzzy")).toHaveLength(3);
    // Both ends are still drawn, one at each side of the cells.
    expect(pace).toHaveTextContent("Calm");
    expect(pace).toHaveTextContent("Buzzy");
  });

  test("test_a_vibe_that_runs_one_way_says_the_end_an_area_sits_at_once_to_a_screen_reader", () => {
    // Recorded: one result sits at the least of a vibe that was asked for, and at the most of
    // one that was not.
    const ranked = recordedAnswer("rank", "rank-first").body.data.ranked;
    const marks = ranked.find((area) => area.area_id === "syn-n0004")?.strip ?? [];
    render(<Strip marks={marks} tags={meta.tags} of="Dulcimer Green" />);
    const drawn = (label: string) => screen.getAllByRole("listitem").find((mark) => mark.textContent?.includes(label));
    const [quiet, family] = [drawn("Quiet streets"), drawn("Family amenities")];

    expect(markOf("quiet_residential", marks)).toMatchObject({ asked: true, band: 1 });
    expect(markOf("family_amenities", marks)).toMatchObject({ asked: false, band: 5 });
    // The word for the end is drawn beside the cells, and is said by the picture.
    expect(quiet).toHaveTextContent(STRIP.least);
    expect(family).toHaveTextContent(STRIP.most);
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

  test("test_that_marks_were_asked_for_is_said_once_before_them_and_of_each_to_a_screen_reader", () => {
    // Said beside every mark, it took a line of every result on a phone.
    const four = recordedAnswer("rank", "rank-first").body.data.ranked[0]?.strip ?? [];
    render(<Strip marks={four} tags={meta.tags} of="Farrowmere" />);
    const marks = screen.getAllByRole("listitem");

    expect(four.map((mark) => mark.asked)).toEqual([true, true, false, false]);
    // For the eye: once before the first that was asked for, and once before the first that was not.
    expect(marks.map((mark) => mark.querySelector("[class*='group'][aria-hidden='true']")?.textContent ?? null)).toEqual([
      STRIP.group.asked,
      null,
      STRIP.group.also,
      null,
    ]);
    // For a screen reader: of each mark that was asked for, and of no other.
    expect(marks.map((mark) => pictureIn(mark).endsWith(STRIP.asked))).toEqual([true, true, false, false]);
  });

  test("test_a_strip_of_which_nothing_was_asked_for_says_nothing_of_asking", () => {
    const none = (recordedAnswer("rank", "rank-first").body.data.ranked[0]?.strip ?? []).map((mark) => ({
      ...mark,
      asked: false,
    }));
    const { container } = render(<Strip marks={none} tags={meta.tags} of="Farrowmere" />);

    expect(none.length).toBeGreaterThan(0);
    expect(container.textContent?.includes(STRIP.group.asked)).toBe(false);
    expect(container.textContent?.includes(STRIP.group.also)).toBe(false);
  });

  test("test_a_vibe_that_runs_one_way_is_counted_from_least_to_most", () => {
    const leafy = recordedAnswer("rank", "rank-shelf").body.data.ranked[0];
    render(<Strip marks={leafy?.strip ?? []} tags={meta.tags} of="Brackenhythe" />);

    expect(pictureIn(screen.getAllByRole("listitem")[0])).toContain(STRIP.from(STRIP.least, STRIP.most));
    expect(pictureIn(screen.getAllByRole("listitem")[0])).toContain(STRIP.asked);
    expect(screen.getAllByRole("listitem")[0]).toHaveTextContent(STRIP.group.asked);
  });

  test("test_a_vibe_that_runs_one_way_says_in_a_word_which_end_the_area_sits_at", () => {
    // Seen by a reviewer: a vibe that runs one way had no word at either end of its picture,
    // so one filled box at the left could be praise or a warning.
    const oneWay = meta.tags.find((tag) => tag.shape === "one_way");
    const at = (band: number) =>
      ({ ...markOf("pace"), tag_id: oneWay?.tag_id, band, spread_low: band, spread_high: band, asked: false, toward: null }) as StripMark;

    // What is drawn beside the name of the vibe, for an area in each of the five bands.
    const words = [1, 2, 3, 4, 5].map((band) => {
      const { container, unmount } = render(<Strip marks={[at(band)]} tags={meta.tags} of={`Band ${band}`} />);
      const word = [...container.querySelectorAll("span")]
        .filter((part) => part.children.length === 0 && part.closest("[role='img']") === null)
        .map((part) => part.textContent)
        .filter((text) => text !== oneWay?.label);
      unmount();
      return word;
    });
    expect(words).toEqual([[STRIP.least], [], [], [], [STRIP.most]]);
  });

  test("test_a_mixed_area_on_a_vibe_that_runs_one_way_is_said_to_sit_at_neither_end", () => {
    const oneWay = meta.tags.find((tag) => tag.shape === "one_way");
    const mixedUp = {
      ...markOf("pace"),
      tag_id: oneWay?.tag_id,
      band: 5,
      spread_low: 3,
      spread_high: 5,
      asked: false,
      toward: null,
    } as StripMark;
    const { container } = render(<Strip marks={[mixedUp]} tags={meta.tags} of="Anywhere" />);

    expect(container.textContent).toBe(oneWay?.label);
  });

  test("test_what_is_left_of_a_strip_whose_first_mark_stands_beside_its_sentence_is_said_to_be_beside_it", () => {
    const leafy = recordedAnswer("rank", "rank-shelf").body.data.ranked[0];
    const others = (leafy?.strip ?? []).filter((mark) => !mark.asked);
    render(<Strip marks={others} tags={meta.tags} of="Brackenhythe" also />);

    expect(others.length).toBeGreaterThan(0);
    expect(screen.getAllByRole("listitem")[0]).toHaveTextContent(STRIP.group.also);
    expect(screen.getAllByRole("listitem").slice(1).filter((one) => one.textContent?.includes(STRIP.group.also))).toEqual([]);
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

  test("test_on_a_narrow_screen_the_strip_holds_what_was_asked_for_and_the_others_give_way", () => {
    // Seen on a phone: four marks took four lines of every card, two of them of vibes nobody
    // asked for, and the first result did not fit the screen. They are on the page of the area.
    const four = recordedAnswer("rank", "rank-first").body.data.ranked[1]?.strip ?? [];
    const { unmount } = render(<Strip marks={four} tags={meta.tags} of="Farrowmere" />);
    const rules = rulesOf(readFileSync(path.join(__dirname, "Strip.module.css"), "utf8"));
    const gives = rules.filter((rule) => rule.sets.get("display") === "none");

    expect(four.map((mark) => mark.asked)).toEqual([true, true, false, false]);
    // The strip says that something was asked for, and each mark whether it was.
    expect(screen.getByRole("list")).toHaveAttribute("data-asked", "true");
    expect(screen.getAllByRole("listitem").map((item) => item.getAttribute("data-asked"))).toEqual([
      "true",
      "true",
      "false",
      "false",
    ]);
    // Only on a narrow screen, only where something was asked for, and only what was not.
    expect(gives.length).toBe(1);
    expect(gives[0]?.under).toMatch(/max-width:\s*40rem/);
    expect(gives[0]?.selector).toBe('.strip[data-asked="true"] .item[data-asked="false"]');

    // Where nothing was asked for, the strip holds what the API chose, at every width.
    unmount();
    const none = render(
      <Strip marks={four.map((mark) => ({ ...mark, asked: false, toward: null }))} tags={meta.tags} of="Farrowmere" />,
    );
    expect(screen.getByRole("list")).toHaveAttribute("data-asked", "false");
    // Where what was asked for stands beside its sentence, the others still give way to it.
    none.unmount();
    render(<Strip marks={four.filter((mark) => !mark.asked)} tags={meta.tags} of="Farrowmere" also />);
    expect(screen.getByRole("list")).toHaveAttribute("data-asked", "true");
  });

  test("test_the_last_word_of_a_mark_that_opens_stands_clear_of_its_edge", () => {
    // Seen in a browser: the name of the end of a scale sat 1 px from the edge of its button.
    const rules = rulesOf(readFileSync(path.join(__dirname, "Strip.module.css"), "utf8"));
    const opens = rules.filter((rule) => /\.opens\[class\]\s*>\s*button$/.test(rule.selector) && rule.under === null);

    expect(opens.map((rule) => rule.sets.get("padding"))).toEqual(["0 var(--space-1) 0 0"]);
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
    render(<Strip marks={[stranger, markOf("pace")]} tags={meta.tags} of="Alderwick" />);

    expect(screen.getAllByRole("listitem")).toHaveLength(1);
  });

  test("test_with_no_mark_there_is_no_strip", () => {
    const { container } = render(<Strip marks={[]} tags={meta.tags} of="Alderwick" />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_a_mark_whose_fact_is_in_hand_opens_to_it_with_its_source", async () => {
    const user = userEvent.setup({ delay: null });
    const { container } = render(<Strip marks={first.strip} tags={meta.tags} facts={facts} of="Alderwick" />);
    const pace = screen.getAllByRole("button")[0] as HTMLElement;

    expect(pace).toHaveAttribute("aria-expanded", "false");
    await user.click(pace);

    const fact = facts[markOf("pace").fact_id] as Fact;
    const opened = within(screen.getByRole("group", { name: fact.label }));
    expect(opened.getByText(fact.slots.judgement ?? "")).toBeInTheDocument();
    expect(opened.getByRole("button", { name: /^Source/ })).toBeInTheDocument();
    // Every figure it shows is a slot of the fact, or the band the mark itself holds.
    const allowed = new Set([...saidBy([fact]), ...first.strip.map(inWords)]);
    expect(figuresNotFrom(container, allowed)).toEqual([]);
  });

  test("test_a_mark_whose_fact_is_not_in_hand_is_not_a_button", () => {
    render(<Strip marks={first.strip} tags={meta.tags} of="Alderwick" />);

    expect(screen.queryAllByRole("button")).toHaveLength(0);
  });

  test("test_the_strip_has_no_fault_an_automated_check_can_find", async () => {
    const { container } = render(<Strip marks={first.strip} tags={meta.tags} facts={facts} of="Alderwick" />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
