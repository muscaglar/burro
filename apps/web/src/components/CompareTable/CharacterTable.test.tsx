import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RESTS_ON } from "@/content/bands";
import { COMPARE_TABLE } from "@/content/compare";
import { CANNOT_PLACE, FACT_COLUMNS } from "@/content/facts";
import { KNOWN } from "@/content/kit";
import { SOURCE, STRIP } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { CompareData } from "@/lib/api/schema";

import { CRIME_ACCOUNT, crimeVibes } from "@/content/crime";
import { CRIME_CAVEAT } from "@/content/settings";
import { plainly } from "@/lib/vibes";

import { faultsIn } from "../../../test/support/axe";
import { heavier, rulesOf, weightOf } from "../../../test/support/css";
import { ROUGH } from "../../../test/support/rough";
import { picturesAtEnds } from "../kit/Ends/picture";
import { CharacterTable } from "./CharacterTable";
import { ENDS_MAY_STAND, ENDS_STAND, UNDER_A_GAUGE, UNDER_A_GAUGE_MAY_STAND } from "./look";

const { tags, features } = recordedAnswer("get_meta", "meta").body.data;
const crime = crimeVibes({ tags, features });
const three: CompareData = recordedAnswer("compare", "compare-three").body.data;
const two: CompareData = recordedAnswer("compare", "compare-two-defaults").body.data;
/** Four areas, of which the last can be placed on one vibe of the fourteen. */
const four: CompareData = recordedAnswer("compare", "compare-two-journeys").body.data;
const LAST = four.areas.length - 1;

const table = () => screen.getByRole("table", { name: COMPARE_TABLE.character.caption });
const rows = () => within(table()).getAllByRole("row").slice(1);
const labelOf = (tagId: string) => tags.find((tag) => tag.tag_id === tagId)?.label ?? "";
/** Which of the five cells of a mark are filled, from the low end to the high end. */
const filled = (cell: HTMLElement) =>
  [...cell.querySelectorAll("[data-on]")].map((one) => one.getAttribute("data-on") === "true");
/**
 * What a cell says of where its area sits, to whoever sees it and to whoever hears it: the
 * words that are drawn in it, and the name of its picture where the picture says them.
 */
const saidIn = (cell: HTMLElement) =>
  [cell.textContent ?? "", ...within(cell).queryAllByRole("img").map((picture) => picture.getAttribute("aria-label") ?? "")].join(" ");
/** The drawings a cell shows, in the order they stand, by where each is served from. */
const drawnIn = (part: HTMLElement) =>
  [...part.querySelectorAll<HTMLElement>("[style*='/art/']")].map((one) => one.style.getPropertyValue("--art"));
const served = (name: string) => `url("/art/${name}.png")`;

describe("the character of the areas compared", () => {
  test("test_there_is_one_row_for_each_vibe_the_api_compares_in_the_order_it_gave", () => {
    render(<CharacterTable data={three} tags={tags} />);

    expect(rows().map((row) => within(row).getByRole("rowheader").querySelector("span")?.textContent)).toEqual(
      three.character.map((row) => labelOf(row.tag_id)),
    );
    expect(three.character).toHaveLength(14);
  });

  test("test_there_is_one_column_for_each_area_under_its_name", () => {
    render(<CharacterTable data={three} tags={tags} />);

    const headers = within(table()).getAllByRole("columnheader").map((header) => header.textContent);

    expect(headers).toEqual([COMPARE_TABLE.character.what, ...three.areas.map((area) => area.name)]);
    for (const row of rows()) expect(within(row).getAllByRole("cell")).toHaveLength(three.areas.length);
  });

  test.each(UNDER_A_GAUGE_MAY_STAND)(
    "test_each_area_is_marked_on_the_line_of_each_vibe_and_its_band_is_said_in_words_with_%s_under_its_gauge",
    (under) => {
      render(<CharacterTable data={two} tags={tags} under={under} />);

      two.character.forEach((vibe, at) => {
        const cells = within(rows()[at] as HTMLElement).getAllByRole("cell");
        vibe.marks.forEach((mark, column) => {
          const cell = cells[column] as HTMLElement;
          if (mark.band === null) throw new Error("Both areas are placed on every vibe.");
          expect(filled(cell).map((on, band) => (on ? band + 1 : 0)).filter(Boolean)).toEqual([mark.band]);
          // In words that are drawn under the gauge, or by the name of the picture, which
          // whoever hears the page hears: and never by both, which would say it twice.
          const pictures = within(cell).queryAllByRole("img");
          if (under === "words") {
            expect(cell).toHaveTextContent(STRIP.band(mark.band));
            expect(pictures).toEqual([]);
          } else {
            expect(pictures).toHaveLength(1);
            expect(pictures[0]?.getAttribute("aria-label")?.includes(STRIP.band(mark.band))).toBe(true);
            expect(cell.textContent?.includes(STRIP.band(mark.band))).toBe(false);
          }
        });
      });
    },
  );

  test("test_a_page_that_hands_nothing_has_the_gauges_as_the_lines_that_choose_say", () => {
    render(<CharacterTable data={two} tags={tags} />);

    expect(table()).toHaveAttribute("data-under", UNDER_A_GAUGE);
    expect(table()).toHaveAttribute("data-ends", ENDS_STAND);
    // A cell is small, and its gauge says where the area sits: nothing is said under it.
    expect(UNDER_A_GAUGE).toBe("nothing");
  });

  test("test_a_scale_names_its_two_ends_and_a_vibe_that_runs_one_way_runs_from_least_to_most", () => {
    render(<CharacterTable data={two} tags={tags} />);

    const header = (label: string) =>
      within(table())
        .getAllByRole("rowheader")
        .find((one) => one.querySelector("span")?.textContent === label);

    expect(header("Going out")).toHaveTextContent(COMPARE_TABLE.character.ends("Calm", "Buzzy"));
    expect(header("Leafy")).toHaveTextContent(COMPARE_TABLE.character.ends(STRIP.least, STRIP.most));
    // It says it as the page of an area does, and in no word of the design: "counted from
    // least to most" stood under every vibe, and was read twice.
    expect(COMPARE_TABLE.character.ends("Calm", "Buzzy")).toBe(`${FACT_COLUMNS.ends} Calm ${FACT_COLUMNS.to} Buzzy`);
    expect(table().textContent?.includes("counted from")).toBe(false);
  });

  test("test_an_area_a_vibe_cannot_place_says_so_and_is_never_put_in_the_middle", () => {
    render(<CharacterTable data={four} tags={tags} />);
    const pace = four.character.findIndex((row) => row.tag_id === "pace");

    const cells = within(rows()[pace] as HTMLElement).getAllByRole("cell");

    expect(four.character[pace]?.marks.map((mark) => mark.band)).toEqual([5, 1, 1, null]);
    expect(cells[LAST]).toHaveTextContent(COMPARE_TABLE.character.notPlaced);
    expect(filled(cells[LAST] as HTMLElement)).toEqual([]);
    expect(/band \d/.test(saidIn(cells[LAST] as HTMLElement))).toBe(false);
    expect(within(cells[LAST] as HTMLElement).queryAllByRole("img")).toEqual([]);
    expect(saidIn(cells[1] as HTMLElement).includes(STRIP.band(1))).toBe(true);
  });

  test("test_an_area_that_cannot_be_placed_says_so_once_with_why_and_not_in_every_row", () => {
    const { container } = render(<CharacterTable data={four} tags={tags} />);
    const last = four.areas[LAST];
    const unplaced = four.character.filter((row) => row.marks[LAST]?.band === null).length;

    // Burro places the last area on one vibe of the fourteen.
    expect(unplaced).toBe(13);
    expect(container.textContent?.split(COMPARE_TABLE.character.unplaced(last?.name ?? "", 13, 14))).toHaveLength(2);
    expect(container.textContent?.split(COMPARE_TABLE.character.unplacedWhy)).toHaveLength(2);
    // It is said under the table, in sight: where the areas sit comes first, and a cell says
    // in two words that an area is not placed.
    const note = screen.getByText(COMPARE_TABLE.character.unplaced(last?.name ?? "", 13, 14));
    expect(table().compareDocumentPosition(note) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(note.closest(".visually-hidden, [hidden], [aria-hidden='true'], details")).toBeNull();
    // The long line is in no cell. A cell says in two words that the area is not placed.
    expect(table().textContent?.includes(CANNOT_PLACE)).toBe(false);
    const cells = rows().flatMap((row) => within(row).getAllByRole("cell")[LAST] as HTMLElement);
    expect(cells.filter((cell) => cell.textContent?.includes(COMPARE_TABLE.character.notPlaced))).toHaveLength(13);
    // The areas Burro places on every vibe are said nothing of. The third has no figure for
    // its high street, so it cannot be placed on Village feel, and that is said of it once.
    const placedOnAll = four.areas.filter((_, at) => four.character.every((row) => row.marks[at]?.band !== null));
    expect(placedOnAll.map((area) => area.name)).toEqual(["Wexmoor", "Marrowfen"]);
    const saidOf = (name: string) =>
      Array.from({ length: 14 }, (_, at) => COMPARE_TABLE.character.unplaced(name, at + 1, 14)).filter((line) =>
        container.textContent?.includes(line),
      );
    for (const area of placedOnAll) expect([area.name, saidOf(area.name)]).toEqual([area.name, []]);
    expect(saidOf("Gorsebeck")).toEqual([COMPARE_TABLE.character.unplaced("Gorsebeck", 1, 14)]);
  });

  test("test_with_every_area_placed_on_every_vibe_nothing_is_said_of_placing", () => {
    const { container } = render(<CharacterTable data={two} tags={tags} />);

    for (const area of two.areas) {
      for (let count = 1; count <= 14; count += 1) {
        expect(container.textContent?.includes(COMPARE_TABLE.character.unplaced(area.name, count, 14))).toBe(false);
      }
    }
    expect(container.textContent?.includes(COMPARE_TABLE.character.unplacedWhy)).toBe(false);
  });

  test.each(UNDER_A_GAUGE_MAY_STAND)(
    "test_where_an_area_sits_is_said_in_words_a_person_would_use_beside_the_band_with_%s_under_its_gauge",
    (under) => {
      render(<CharacterTable data={two} tags={tags} under={under} />);

      two.character.forEach((vibe, at) => {
        const tag = tags.find((one) => one.tag_id === vibe.tag_id);
        const cells = within(rows()[at] as HTMLElement).getAllByRole("cell");
        vibe.marks.forEach((mark, column) => {
          if (mark.band === null || tag === undefined) throw new Error("Both areas are placed on every vibe.");
          const words = plainly(tag, { band: mark.band, spread_low: mark.band, spread_high: mark.band });
          const said = saidIn(cells[column] as HTMLElement);
          expect(said.includes(`${words ?? "no words"}, ${STRIP.band(mark.band)}`)).toBe(true);
          // Once: drawn under the gauge, or said by its picture.
          expect(said.split(STRIP.band(mark.band))).toHaveLength(2);
        });
      });
    },
  );

  /** A band rests on part of what goes into its vibe where the two counts of its fact differ. */
  const restsOnPart = (data: CompareData, factId: string) => {
    const { known, parts } = data.facts.find((one) => one.fact_id === factId)?.slots ?? {};
    return known !== undefined && parts !== undefined && known !== parts;
  };

  test.each(UNDER_A_GAUGE_MAY_STAND)(
    "test_a_band_that_rests_on_part_says_approx_data_after_the_mark_of_what_is_not_whole_as_a_result_does_with_%s_under_its_gauge",
    (under) => {
      render(<CharacterTable data={two} tags={tags} under={under} />);

      two.character.forEach((vibe, at) => {
        const cells = within(rows()[at] as HTMLElement).getAllByRole("cell");
        vibe.marks.forEach((mark, column) => {
          const cell = cells[column] as HTMLElement;
          const onPart = restsOnPart(two, mark.fact_id);
          const said = [...cell.querySelectorAll<HTMLElement>("[data-known='some']")];
          // Once, where the band rests on part, and in no cell of a band that rests on the whole.
          expect([vibe.tag_id, column, said.map((one) => one.textContent)]).toEqual([vibe.tag_id, column, onPart ? [KNOWN.some] : []]);
          expect([vibe.tag_id, column, cell.textContent?.includes(KNOWN.some)]).toEqual([vibe.tag_id, column, onPart]);
          if (!onPart) return;
          // The mark is dress, and the two words are read and heard.
          const drawn = said[0]?.querySelector<HTMLElement>("[style*='/art/']");
          expect(drawn?.style.getPropertyValue("--art")).toBe(served("ui-approx"));
          expect(drawn).toHaveAttribute("aria-hidden", "true");
          expect(said[0]?.closest("[aria-hidden='true'], .visually-hidden")).toBeNull();
        });
      });
      // Both are in the recording, so both are held.
      const all = two.character.flatMap((vibe) => vibe.marks.map((mark) => restsOnPart(two, mark.fact_id)));
      expect(new Set(all)).toEqual(new Set([true, false]));
    },
  );

  test("test_what_a_band_rests_on_is_left_to_the_page_of_the_area_whatever_its_fact_says_of_it", () => {
    // A cell is small. It says that the band is not whole, in two words: how many of the
    // measurements it rests on, and which are missing, is on the page of the area, which
    // the name of the area leads to. So neither the clause of the service nor the counts
    // in the words of the website stand in a cell.
    const clause = "Worked out from 2 of its 3 parts, 75 of 100 by weight.";
    const resting = two.facts.filter((fact) => fact.kind === "tag" && restsOnPart(two, fact.fact_id));
    expect(resting.length).toBeGreaterThan(0);
    const told: CompareData = {
      ...two,
      facts: two.facts.map((fact) => (resting.includes(fact) ? { ...fact, slots: { ...fact.slots, share: "75", partly: clause } } : fact)),
    };
    const bare: CompareData = {
      ...two,
      facts: two.facts.map((fact) => ({
        ...fact,
        slots: Object.fromEntries(Object.entries(fact.slots).filter(([slot]) => slot !== "partly")),
      })),
    };

    for (const data of [two, told, bare]) {
      const { unmount } = render(<CharacterTable data={data} tags={tags} />);
      const said = table().textContent ?? "";
      expect(said.includes(clause)).toBe(false);
      expect(/measurements|of its \d+ parts/.test(said)).toBe(false);
      for (const fact of resting) {
        expect(said.includes(RESTS_ON.short(fact.slots.known ?? "", fact.slots.parts ?? ""))).toBe(false);
      }
      expect(said.split(KNOWN.some).length - 1).toBe(data.character.flatMap((vibe) => vibe.marks).filter((mark) => restsOnPart(data, mark.fact_id)).length);
      unmount();
    }
  });

  test("test_the_step_of_a_band_that_rests_on_part_of_its_recipe_is_chequered_as_it_is_on_a_result", () => {
    render(<CharacterTable data={two} tags={tags} />);

    two.character.forEach((vibe, at) => {
      const cells = within(rows()[at] as HTMLElement).getAllByRole("cell");
      vibe.marks.forEach((mark, column) => {
        const onPart = restsOnPart(two, mark.fact_id);
        const line = cells[column]?.querySelector("[data-part]");
        expect([vibe.tag_id, column, line?.getAttribute("data-part")]).toEqual([vibe.tag_id, column, String(onPart)]);
        // It is said in words as well: the chequer is never all that says it, and no cell
        // says it of a band that rests on the whole.
        expect([vibe.tag_id, column, (cells[column]?.textContent ?? "").includes(KNOWN.some)]).toEqual([vibe.tag_id, column, onPart]);
      });
    });
    // Both are in the recording, so both are held.
    const drawn = [...table().querySelectorAll("[data-part]")].map((line) => line.getAttribute("data-part"));
    expect(new Set(drawn)).toEqual(new Set(["true", "false"]));
  });

  test.each(ENDS_MAY_STAND)("test_each_end_of_a_gauge_has_its_one_picture_and_the_two_are_opposites_where_the_ends_stand_at_the_%s", (ends) => {
    render(<CharacterTable data={three} tags={tags} ends={ends} />);

    three.character.forEach((vibe, at) => {
      const tag = tags.find((one) => one.tag_id === vibe.tag_id);
      if (tag === undefined) throw new Error("The release names every vibe of the comparison.");
      const [low, high] = picturesAtEnds(tag.tag_id).map(served);
      // The two are opposites, and every vibe of the release has a pair of its own.
      expect([tag.tag_id, low === high]).toEqual([tag.tag_id, false]);
      const row = rows()[at] as HTMLElement;
      const head = within(row).getByRole("rowheader");
      const gauges = [...row.querySelectorAll<HTMLElement>("td .gauge")];
      expect(gauges).toHaveLength(vibe.marks.filter((mark) => mark.band !== null).length);
      for (const gauge of gauges) {
        const parts = [...gauge.children].map((part) => (part.matches("[data-placed]") ? "steps" : (part as HTMLElement).style.getPropertyValue("--art")));
        // At either end of every gauge, the low end first as the steps run: or the steps alone.
        expect([tag.tag_id, parts]).toEqual([tag.tag_id, ends === "gauge" ? [low, "steps", high] : ["steps"]]);
        // The pictures are dress, and say nothing to whoever hears the page.
        for (const picture of gauge.querySelectorAll<HTMLElement>(":scope > [style*='/art/']:not([data-placed])")) {
          expect(picture).toHaveAttribute("aria-hidden", "true");
        }
      }
      // Once at the head of the row, each over the name of its end: or in words alone.
      const atTheHead = drawnIn(head).filter((drawing) => drawing === low || drawing === high);
      expect([tag.tag_id, atTheHead]).toEqual([tag.tag_id, ends === "row" ? [low, high] : []]);
      const [first, last] = [tag.low_end ?? STRIP.least, tag.high_end ?? STRIP.most];
      expect(head.textContent?.replace(/\s+/g, " ").includes(COMPARE_TABLE.character.ends(first, last))).toBe(true);
    });
  });

  test("test_the_small_drawing_of_a_vibe_stands_with_its_name_at_the_head_of_its_row", () => {
    render(<CharacterTable data={three} tags={tags} />);

    three.character.forEach((vibe, at) => {
      const tag = tags.find((one) => one.tag_id === vibe.tag_id);
      const head = within(rows()[at] as HTMLElement).getByRole("rowheader");
      const named = head.firstElementChild as HTMLElement;
      // Its drawing first, which is chosen by what the service calls the vibe, and then its name.
      expect([vibe.tag_id, /^url\("\/art\/thing-[a-z-]+\.png"\)$/.test(drawnIn(named)[0] ?? "")]).toEqual([vibe.tag_id, true]);
      expect([vibe.tag_id, drawnIn(named).length]).toEqual([vibe.tag_id, 1]);
      expect(named.textContent).toBe(tag?.label);
      // It is dress. The name is heard as it was, once, and the drawing says nothing.
      expect(named.querySelector("[style*='/art/']")?.closest("[aria-hidden='true']")).not.toBeNull();
      expect(within(named).queryAllByRole("img")).toEqual([]);
    });
  });

  test("test_the_table_says_how_many_areas_stand_side_by_side", () => {
    render(<CharacterTable data={four} tags={tags} />);

    expect(table()).toHaveAttribute("data-areas", String(four.areas.length));
    // It is a table of a comparison, and the one of the two whose areas stand side by side on every screen.
    expect(table().className.split(/\s+/)).toEqual(["table", "character"]);
  });

  test("test_a_mixed_area_is_drawn_as_a_range_and_said_to_vary", () => {
    const mixed: CompareData = {
      ...two,
      character: two.character.map((row) =>
        row.tag_id !== "pace"
          ? row
          : { ...row, marks: row.marks.map((mark, at) => (at === 0 ? { ...mark, band: 4, spread_low: 3, spread_high: 5 } : mark)) },
      ),
    };
    render(<CharacterTable data={mixed} tags={tags} />);
    const pace = mixed.character.findIndex((row) => row.tag_id === "pace");

    const cell = within(rows()[pace] as HTMLElement).getAllByRole("cell")[0] as HTMLElement;

    expect(within(cell).getByRole("img")).toHaveAccessibleName(STRIP.bands(3, 5));
    expect(filled(cell)).toEqual([false, false, true, true, true]);
  });

  test("test_no_vibe_is_shown_as_a_percentage_a_score_or_a_rank", () => {
    render(<CharacterTable data={three} tags={tags} />);

    expect(/%|percent|score|rank/i.test(table().textContent ?? "")).toBe(false);
  });

  test("test_a_vibe_that_cannot_place_an_area_has_nothing_to_press_in_its_cell", () => {
    render(<CharacterTable data={four} tags={tags} />);

    const cells = rows().flatMap((row) => within(row).getAllByRole("cell"));
    const unplaced = cells.filter((cell) => cell.textContent?.includes(COMPARE_TABLE.character.notPlaced));

    // Thirteen of the last area, and one of the third, which has no figure for its high street.
    expect(unplaced).toHaveLength(14);
    for (const cell of unplaced) expect(within(cell).queryByRole("button")).toBeNull();
  });

  test("test_a_vibe_the_service_calls_a_rough_guide_is_a_row_as_any_other_and_nothing_says_that_it_is_one", () => {
    // The founder, who had walked the website twice: "remove the concept of rough guide, we
    // don't want to pass this on to a user". The service still says which vibe it holds to
    // be less sure than the rest, in a code. The table is handed the vibes of the release
    // and nothing else of it, so no word of a service reaches it: it is held to write none
    // of its own, neither the label a service gave such a vibe nor the sentence that said why.
    const guide = tags.find((tag) => tag.tag_id === ROUGH.tag_id);
    if (guide === undefined) throw new Error("the recorded release holds no such vibe");
    render(<CharacterTable data={three} tags={tags} />);

    expect(guide.sureness).toBe("rough_guide");
    const row = rows().find((one) => within(one).getByRole("rowheader").querySelector("span")?.textContent === guide.label);
    if (row === undefined) throw new Error("the comparison draws no row of the vibe");
    // Its head holds what the head of any vibe holds: its name, its two ends, and its source.
    const head = within(row).getByRole("rowheader");
    expect([...head.children].map((part) => part.className || part.tagName)).toEqual(["named", "visually-hidden", "weight", "source"]);
    expect(head).toHaveTextContent(COMPARE_TABLE.character.ends(STRIP.least, STRIP.most));
    // Neither its label nor the sentence that said why stands anywhere in the table.
    expect(table().querySelector("[data-rough-guide]")).toBeNull();
    expect(table().textContent?.includes(ROUGH.label)).toBe(false);
    expect(table().textContent?.includes(ROUGH.why)).toBe(false);
    expect(/rough|less sure/i.test(table().textContent ?? "")).toBe(false);
  });

  test("test_the_table_is_handed_nothing_a_rough_guide_says_of_itself_and_reads_no_word_of_one", () => {
    const written = ["CharacterTable.tsx", "CompareTable.tsx", "CompareView.tsx", "VibeMark.tsx", "towns.ts", "CompareTable.module.css", "CompareView.module.css"]
      .map((file) => readFileSync(path.join(__dirname, file), "utf8"))
      .join("\n");

    expect(/rough|sureness|RoughGuide/i.test(written)).toBe(false);
  });

  test("test_the_head_of_a_row_is_named_by_its_vibe_alone_and_holds_what_else_is_said_of_it", () => {
    // Heard by keyboard: every cell of a row was read under the whole of its head, its name,
    // its two ends, the name of its source and every note that stood in it, since the head
    // of a row is named by all that is in it. It is named by its vibe, and the rest is read in it.
    render(<CharacterTable data={three} tags={tags} crime={crime} />);

    const heads = within(table()).getAllByRole("rowheader");

    expect(heads.map((head) => head.getAttribute("aria-labelledby") !== null)).toEqual(heads.map(() => true));
    for (const [at, head] of heads.entries()) {
      expect(head).toHaveAccessibleName(labelOf(three.character[at]?.tag_id ?? ""));
    }
    // No two heads are named by one part of the page.
    expect(new Set(heads.map((head) => head.getAttribute("aria-labelledby"))).size).toBe(heads.length);
    // What is said of the vibe is in the head all the same, in sight and for whoever reads into it.
    const village = heads.find((head) => head.querySelector("span")?.textContent === "Village feel") as HTMLElement;
    expect(village).toHaveTextContent(COMPARE_TABLE.character.ends(STRIP.least, STRIP.most));
    expect(within(village).getByRole("button", { name: SOURCE.buttonFor("Village feel") })).toBeInTheDocument();
  });

  test("test_every_vibe_gives_its_source_and_its_date_once_in_its_row_for_every_area_it_places", async () => {
    // A key beside every mark was fifty-six keys where four areas are compared, and each
    // opened to the same recipe, the same sources and the same date as the key beside it.
    const user = userEvent.setup({ delay: null });
    render(<CharacterTable data={two} tags={tags} />);

    const buttons = within(table()).getAllByRole("button", { name: /^Source for / });

    // One for each vibe, in the head of its row, and no two of one name.
    expect(buttons).toHaveLength(two.character.length);
    expect(buttons.map((button) => button.getAttribute("aria-label"))).toEqual(
      two.character.map((row) => SOURCE.buttonFor(labelOf(row.tag_id))),
    );
    for (const button of buttons) expect(button.closest("th")).toHaveAttribute("role", "rowheader");
    await user.click(buttons[0] as HTMLElement);
    const behind = (two.character[0]?.marks ?? []).map((mark) => two.facts.find((one) => one.fact_id === mark.fact_id));
    const head = (buttons[0] as HTMLElement).closest("th") as HTMLElement;
    // Each source is named once and each date once, however many areas the vibe places.
    for (const fact of behind) {
      expect(within(head).getAllByRole("link", { name: fact?.sources[0]?.name })).toHaveLength(1);
      expect(head.textContent?.split(`${SOURCE.dataFrom} ${fact?.as_of}`)).toHaveLength(2);
    }
    expect(within(head).getByRole("link", { name: behind[0]?.sources[0]?.name })).toHaveAttribute(
      "href",
      `/sources#${behind[0]?.sources[0]?.source_id}`,
    );
    expect(head).toHaveTextContent(SOURCE.madeUp);
    // Whose recipe it is, and that its weights are a judgement, in the API's own words.
    expect(head).toHaveTextContent(behind[0]?.slots.judgement ?? "no judgement");
  });

  test("test_the_facts_of_a_vibe_are_of_one_recipe_and_one_date_for_every_area_so_that_one_source_says_all_of_it", () => {
    // Held of every comparison that was recorded: were the facts of one vibe to differ in
    // their sources or their date by area, a source given once would still name each once.
    for (const data of [two, three, four]) {
      for (const row of data.character) {
        // Of each area the vibe places: a fact that places no area holds no figure, and gives no source.
        const behind = row.marks.flatMap((mark) =>
          mark.band === null ? [] : (data.facts.find((one) => one.fact_id === mark.fact_id) ?? []),
        );
        if (behind.length === 0) continue;
        expect(new Set(behind.map((fact) => `${fact.as_of} ${fact.sources.map((source) => source.source_id).join(" ")}`)).size).toBe(1);
        expect(new Set(behind.map((fact) => `${fact.slots.made_from} ${fact.slots.judgement}`)).size).toBe(1);
      }
    }
  });

  test("test_a_vibe_that_places_no_area_of_the_comparison_has_no_source_to_give", () => {
    const none: CompareData = {
      ...two,
      character: two.character.map((row, at) =>
        at === 0 ? { ...row, marks: row.marks.map((mark) => ({ ...mark, band: null, spread_low: null, spread_high: null })) } : row,
      ),
    };
    render(<CharacterTable data={none} tags={tags} />);

    expect(within(rows()[0] as HTMLElement).queryByRole("button")).toBeNull();
    expect(within(rows()[1] as HTMLElement).getAllByRole("button", { name: /^Source for / })).toHaveLength(1);
  });

  test("test_a_mark_whose_fact_did_not_come_is_not_drawn_because_it_would_have_no_source", () => {
    const without: CompareData = { ...two, facts: two.facts.filter((fact) => fact.kind !== "tag") };
    render(<CharacterTable data={without} tags={tags} />);

    for (const row of rows()) {
      for (const cell of within(row).getAllByRole("cell")) {
        expect(filled(cell)).toEqual([]);
        expect(cell).toHaveTextContent(COMPARE_TABLE.noFigure);
      }
    }
  });

  test("test_a_vibe_that_counts_recorded_crime_says_so_in_its_row_with_the_caveat", () => {
    render(<CharacterTable data={two} tags={tags} crime={crime} />);
    const header = (label: string) =>
      within(table())
        .getAllByRole("rowheader")
        .find((one) => one.querySelector("span")?.textContent === label) as HTMLElement;

    expect(header("Gritty")).toHaveTextContent(CRIME_ACCOUNT.counts);
    expect(header("Gritty")).toHaveTextContent("Recorded criminal damage");
    expect(header("Gritty")).toHaveTextContent(CRIME_CAVEAT);
    // No other vibe holds recorded crime, and none says it does.
    expect(table().textContent?.split(CRIME_ACCOUNT.counts)).toHaveLength(2);
    expect(header("Leafy").textContent?.includes(CRIME_CAVEAT)).toBe(false);
  });

  test("test_a_vibe_the_release_does_not_name_has_no_row", () => {
    render(<CharacterTable data={three} tags={tags.filter((tag) => tag.tag_id !== "pace")} />);

    expect(rows()).toHaveLength(13);
    expect(table()).not.toHaveTextContent("Going out");
  });

  test("test_with_no_vibe_to_compare_there_is_no_table", () => {
    const { container } = render(<CharacterTable data={{ ...three, character: [] }} tags={tags} />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_every_part_of_the_table_says_its_role_so_that_it_stays_a_table_when_stacked", () => {
    render(<CharacterTable data={three} tags={tags} />);

    expect(table()).toHaveAttribute("role", "table");
    expect([...table().querySelectorAll("thead, tbody")].map((group) => group.getAttribute("role"))).toEqual([
      "rowgroup",
      "rowgroup",
    ]);
    for (const row of table().querySelectorAll("tr")) expect(row).toHaveAttribute("role", "row");
    for (const cell of table().querySelectorAll("td")) expect(cell).toHaveAttribute("role", "cell");
    for (const header of table().querySelectorAll("thead th")) expect(header).toHaveAttribute("role", "columnheader");
    for (const header of table().querySelectorAll("tbody th")) expect(header).toHaveAttribute("role", "rowheader");
  });

  test("test_each_cell_says_whose_it_is_for_the_eye_and_the_column_says_it_to_a_reader", () => {
    render(<CharacterTable data={three} tags={tags} />);

    for (const row of rows()) {
      const whose = [...row.querySelectorAll("td")].map((cell) => cell.querySelector("[aria-hidden='true']")?.textContent);
      expect(whose).toEqual(three.areas.map((area) => area.name));
    }
  });

  test("test_the_table_has_no_accessibility_fault", async () => {
    const { container } = render(<CharacterTable data={three} tags={tags} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the vibes of the areas, side by side on every screen", () => {
  const STYLES = rulesOf(readFileSync(path.join(__dirname, "CompareTable.module.css"), "utf8"));
  const NARROW = "@media (max-width: 59.99rem)";
  const narrow = (selector: string) =>
    new Map(STYLES.filter((rule) => rule.under === NARROW && rule.selector === selector).flatMap((rule) => [...rule.sets]));

  test("test_what_a_vibe_is_and_how_a_line_is_read_is_said_once_over_the_vibes_in_sight", () => {
    render(<CharacterTable data={three} tags={tags} />);
    const said = screen.getByText(COMPARE_TABLE.character.lead);

    expect(said.tagName).toBe("P");
    expect(said.closest(".visually-hidden, [hidden], [aria-hidden='true'], details")).toBeNull();
    expect(Boolean(said.compareDocumentPosition(table()) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
    // It says what a vibe is, how a line runs, and that neither end is the better one.
    expect(COMPARE_TABLE.character.lead).toMatch(/^A vibe is a way of describing what an area feels like\./);
    expect(COMPARE_TABLE.character.lead).toMatch(/five steps/);
    expect(COMPARE_TABLE.character.lead).toMatch(/Neither end is the better one/);
  });

  test("test_on_a_narrow_screen_a_vibe_has_a_line_of_its_own_and_each_area_a_column_under_it", () => {
    // Measured on a phone, 390 by 844, with four areas compared: stacked, one area under
    // the next, the vibes were 8,439 px high, which is ten screens, and no two areas of a
    // vibe were in sight at once.
    expect([narrow(".table.character .row").get("display"), narrow(".table.character .row").get("grid-template-columns")]).toEqual([
      "grid",
      "repeat(2, minmax(0, 1fr))",
    ]);
    expect(narrow(".table.character .thing").get("grid-column")).toBe("1 / -1");
    // On a phone two stand side by side, and a third and a fourth under them: in a column a
    // quarter of a phone wide a name was broken in two. Where a screen is wider each has a column.
    const between = (selector: string) =>
      STYLES.filter((rule) => rule.under === "@media (min-width: 40.0625rem) and (max-width: 59.99rem)" && rule.selector === selector).flatMap(
        (rule) => rule.sets.get("grid-template-columns") ?? [],
      );
    expect(between('.table.character[data-areas="3"] .row')).toEqual(["repeat(3, minmax(0, 1fr))"]);
    expect(between('.table.character[data-areas="4"] .row')).toEqual(["repeat(4, minmax(0, 1fr))"]);
    // Each weighs more than what is said of every table of a comparison, which is stacked there.
    for (const [mine, theirs] of [
      [".table.character .row", ".row"],
      [".table.character .thing", ".table th"],
      [".table.character .mark", ".table .mark"],
    ] as const) {
      expect([mine, heavier(weightOf(mine), weightOf(theirs))]).toEqual([mine, true]);
    }
    // On a screen narrower than any phone of today half a row has not the room of a gauge
    // with a picture at each end, and each area has the width of the row.
    const narrowest = STYLES.filter((rule) => rule.under === "@media (max-width: 21.99rem)" && rule.selector === ".table.character .row");
    expect(narrowest.map((rule) => rule.sets.get("grid-template-columns"))).toEqual(["minmax(0, 1fr)"]);
    // No area has a column wider than the next, and none is put first: every column is one share.
    const columns = STYLES.filter((rule) => /\.character\b.* \.row$/.test(rule.selector) && rule.sets.has("grid-template-columns"));
    expect(columns.length).toBe(4);
    expect(columns.flatMap((rule) => rule.sets.get("grid-template-columns")?.match(/\d+fr|auto|\d+(px|rem|%)/g) ?? []).filter((size) => size !== "1fr")).toEqual([]);
  });

  test("test_the_steps_of_a_cell_are_the_first_thing_drawn_in_it_so_that_the_steps_of_a_column_stand_one_under_the_next", () => {
    // The founder asked that the five steps of every result stand in one column, so that the
    // eye runs down them, and the same holds wherever five steps stand in rows. Measured in
    // a browser, of three areas compared: at 1440 by 900 every line of the first column
    // began at 444.5 px, of the second at 733.5 px and of the third at 1022.5 px, and at 390
    // by 844, where two stand side by side, at 24 px and at 201 px. What is held here is
    // what makes it so, since no page is laid out in a test.
    render(<CharacterTable data={four} tags={tags} />);
    const lines = [...table().querySelectorAll<HTMLElement>("td [data-placed='true']")];

    expect(lines.length).toBeGreaterThan(20);
    for (const line of lines) {
      const gauge = line.parentElement as HTMLElement;
      const holds = gauge.parentElement as HTMLElement;
      // The gauge comes first in what says where an area sits, and what is said of it after.
      expect([holds.tagName, holds.className, holds.firstElementChild === gauge]).toEqual(["P", "placed", true]);
      // Before the steps stands the picture of the low end alone. It is as wide whatever
      // its vibe, so the steps of one gauge stand under the steps of the gauge over it.
      const before = [...gauge.children].slice(0, [...gauge.children].indexOf(line)) as HTMLElement[];
      expect(before.map((one) => [one.style.getPropertyValue("--w"), one.style.getPropertyValue("--h")])).toEqual([["16", "16"]]);
      // Before the gauge in the cell stands the name of the area alone, which is a line of its own where it is drawn.
      const cell = holds.closest("td") as HTMLElement;
      const over = [...cell.children].slice(0, [...cell.children].indexOf(holds));
      expect(over.map((one) => one.className)).toEqual(["cellName"]);
    }
    // Nothing moves the steps from where their cell begins: no room before them, and no turn to the far side.
    const moves = STYLES.filter(
      (rule) =>
        /(^|\s|>)\.(placed|mark|cell)(\[[^\]]*\])*$/.test(rule.selector) &&
        [...rule.sets].some(
          ([property, value]) =>
            /^(text-align|justify-content|justify-self|justify-items|direction|float|order|margin-inline-start|margin-left|padding-inline-start|padding-left|inset-inline-start|transform)$/.test(
              property,
            ) && !/^(start|left|flex-start|normal|0)$/.test(value),
        ),
    );
    expect(moves.map((rule) => [rule.under, rule.selector])).toEqual([]);
    expect(STYLES.filter((rule) => rule.selector === ".cellName").map((rule) => rule.sets.get("display"))).toContain("none");
  });

  test("test_the_steps_of_a_gauge_are_as_wide_as_its_cell_has_the_room_of_and_a_gauge_is_never_cut", () => {
    // A gauge with a picture at each end is 42 art pixels and five steps wide. Measured on
    // a phone, 390 wide, where two areas stand side by side: a cell is 165 px, and a gauge
    // with steps of seven is 154. So what says where an area sits says how wide it is, and
    // its gauge is drawn with the widest steps it has the room of.
    render(<CharacterTable data={four} tags={tags} />);
    const lines = [...table().querySelectorAll<HTMLElement>("td [data-placed='true']")];

    expect(lines.length).toBeGreaterThan(20);
    // The width of a step is the cell's to say, by its own width, and not the screen's.
    expect(new Set(lines.map((line) => line.getAttribute("data-narrow")))).toEqual(new Set(["false"]));
    const of = (selector: string, under: string | null = null) =>
      new Map(STYLES.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));
    expect(of(".placed").get("container-type")).toBe("inline-size");
    // A drawing is laid in pixels of the screen, two to one of its own in a cell: so the
    // widths are asked in pixels, each a little over the gauge it gives way to.
    const px = 2;
    const wide = (step: number) => px * (16 + 2 + (5 * step + 4 + 2) + 2 + 16);
    expect([wide(9), wide(7), wide(5)]).toEqual([174, 154, 134]);
    expect(of(".placed").get("--px")).toBe("var(--px-ground)");
    expect([...of(".gauge", "@container (max-width: 175px)")]).toEqual([["--track-step", "7"]]);
    expect([...of(".gauge", "@container (max-width: 155px)")]).toEqual([["--track-step", "5"]]);
    // The table gives a line no other size of its own: no width, no height and no turn.
    const ofALine = STYLES.filter((rule) => /\.(character|gauge|placed)\b/.test(rule.selector)).flatMap((rule) => [...rule.sets.keys()]);
    expect(ofALine.filter((property) => /^(--step|--rise|width|height|zoom|scale|transform)/.test(property))).toEqual([]);
  });

  test("test_what_the_table_is_called_is_kept_for_whoever_hears_the_page_and_the_heading_says_it_to_whoever_sees_it", () => {
    render(<CharacterTable data={three} tags={tags} />);

    expect(table().querySelector("caption")).toHaveClass("visually-hidden");
    expect(table()).toHaveAccessibleName(COMPARE_TABLE.character.caption);
  });

  test("test_the_key_of_a_source_stays_where_it_is_when_it_is_pressed_on_a_narrow_screen", async () => {
    // Seen in a browser, 390 wide: the key stood at the far end of the line of its vibe,
    // and pressed it went to the start of the next line, from under the finger. Nothing
    // moves under a press: the row lays out the key and what it opens to, each in its place.
    expect(narrow(".table.character .thing").get("display")).toBe("grid");
    expect(narrow(".table.character .thing").get("grid-template-columns")).toBe("minmax(0, 1fr) auto");
    expect(narrow(".table.character .source > div > button").get("grid-column")).toBe("2");
    expect(narrow(".table.character .source > div > button").get("grid-row")).toBe("1 / span 2");
    expect(narrow(".table.character .source > div > div").get("grid-column")).toBe("1 / -1");
    // No rule of the table reads whether a source is open: where a key stands is the same either way.
    expect(STYLES.filter((rule) => /aria-expanded=|\[open\]/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
    // What the rules count on: the key and what it opens to are the two children of what holds them.
    const user = userEvent.setup({ delay: null });
    render(<CharacterTable data={two} tags={tags} />);
    const key = within(table()).getAllByRole("button", { name: /^Source for / })[0] as HTMLElement;
    const holds = key.closest(".source") as HTMLElement;
    expect(holds.children).toHaveLength(1);
    expect([...(holds.firstElementChild?.children ?? [])].map((one) => one.tagName)).toEqual(["BUTTON", "DIV"]);
    await user.click(key);
    expect([...(holds.firstElementChild?.children ?? [])].map((one) => one.tagName)).toEqual(["BUTTON", "DIV"]);
    expect(holds.firstElementChild?.lastElementChild).toHaveAttribute("id", key.getAttribute("aria-controls"));
  });

  test("test_no_cell_holds_anything_to_press_so_that_a_column_of_a_phone_is_as_narrow_as_a_line", () => {
    render(<CharacterTable data={four} tags={tags} />);

    for (const cell of within(table()).getAllByRole("cell")) {
      expect(cell.querySelectorAll("a, button, input, summary, [tabindex]")).toHaveLength(0);
    }
  });
});
