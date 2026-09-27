import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";

import { ABOUT } from "@/content/about";
import { TOWN } from "@/content/town";
import { readRecorded, recordedAnswer } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";
import { PINS } from "@/lib/map/fill";

import { faultsIn } from "../../../test/support/axe";
import { asWritten } from "../../../test/support/contrast";
import { rulesOf } from "../../../test/support/css";
import { ROUGH, sayingSo } from "../../../test/support/rough";
import { onTheGrass } from "../About/grass";
import { pictureOf, type Drawing } from "../kit/drawings";
import { STEPS } from "../kit/Gauge/filled";
import { drawingOf, PLAIN, type ThingKind } from "../kit/Thing/drawn";
import { groupsOf } from "../SettingsPanel/groups";
import { eachWay } from "../WeightSlider/steps";
import { Key, OTHER_THINGS } from "./Key";
import { TRADE_OFF_MAY_BE_SHOWN, TRADE_OFF_SHOWN } from "./look";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const preview: MetaData = recordedAnswer("get_meta", "preview/meta").body.data;
const variantA: MetaData = (readRecorded("variant-a/meta").body as { data: MetaData }).data;

const SHEETS = ["Key.module.css", "../About/KeyRows.module.css", "BandKey.module.css", "../Town/TownKey.module.css"].map(
  (file) => readFileSync(path.resolve(__dirname, file), "utf8"),
);
const RULES = SHEETS.flatMap((sheet) => rulesOf(sheet));
const setsOf = (selector: string, under: string | null = null) =>
  new Map(RULES.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));

const key = () => screen.getByRole("region", { name: ABOUT.key.title });
const row = (name: string) => {
  const found = key().querySelector<HTMLElement>(`[data-key="${name}"]`);
  if (found === null) throw new Error(`The key has no row "${name}".`);
  return found;
};
/** The drawings a part holds, by the picture each is drawn from, in the order they stand. */
const drawnIn = (part: Element) =>
  [...part.querySelectorAll<HTMLElement>("[style*='/art/']")].map((one) => one.style.getPropertyValue("--art"));
const pictured = (name: Drawing) => `url("${pictureOf(name)}")`;
/** What a row says, in the sentences that stand beside its drawing. */
const saidBy = (name: string) => [...row(name).querySelectorAll(":scope > [data-says] > p")].map((one) => one.textContent);

describe("the key to the drawings", () => {
  test("test_it_is_a_part_of_the_page_in_a_box_of_its_own_under_its_heading_and_none_of_it_is_read_on_the_grass", () => {
    const { container } = render(<Key meta={meta} />);

    expect(key()).toHaveAttribute("data-kind", "box");
    expect(within(key()).getByRole("heading", { level: 2, name: ABOUT.key.title })).toHaveAttribute("id", "key");
    expect(key()).toHaveTextContent(ABOUT.key.lead);
    expect(container.children).toHaveLength(1);
    for (const given of [meta, preview, variantA, { ...meta, tags: [] }]) {
      const drawn = render(<Key meta={given} />);
      expect(onTheGrass(drawn.container)).toEqual([]);
      drawn.unmount();
    }
  });

  test("test_it_is_laid_out_by_where_a_drawing_is_met_and_what_a_town_is_built_of_is_inside_it", () => {
    render(<Key meta={meta} />);

    const groups = within(key()).getAllByRole("heading", { level: 3 });

    // The founder: "The what a town is built of is also useful, mix in with the visuals/icons section."
    expect(groups.map((heading) => heading.textContent)).toEqual([
      ABOUT.key.things.title,
      ABOUT.band.title,
      ABOUT.key.result.title,
      ABOUT.key.map.title,
      TOWN.key.title,
    ]);
    // Each heads a part of the key that a person may be looking for, and is a landmark of it.
    for (const heading of groups) {
      expect(within(key()).getByRole("region", { name: heading.textContent ?? "" })).toContainElement(heading);
    }
    expect(key().querySelector("[data-part='trees']")).not.toBeNull();
  });

  test("test_all_of_it_is_in_sight_and_nothing_of_it_is_behind_a_press", () => {
    const markup = renderToStaticMarkup(<Key meta={meta} />);

    expect(markup).not.toMatch(/<details|<summary|<button|aria-expanded|\shidden[=\s>]/i);
  });

  test("test_every_row_is_a_drawing_with_what_it_means_in_a_sentence_or_two", () => {
    render(<Key meta={meta} />);

    const rows = [...key().querySelectorAll<HTMLElement>("[data-key]")];

    expect(rows.map((one) => one.getAttribute("data-key"))).toEqual([
      "vibes",
      "others",
      "groups",
      "off",
      "gauge",
      "gauge-of-a-scale",
      "cross",
      "one-way",
      "scale",
      "part",
      "mixed",
      "unplaced",
      "carrot",
      "rank",
      "source",
      "trade-off",
      "arrow",
      "notice",
      "fault",
      "greens",
      "sand",
      "dots",
      "lines",
      "water",
      "pin",
      "built-of-trees",
      "built-of-height",
      "built-of-lit",
      "built-of-roofs",
      "built-of-blank",
    ]);
    for (const one of rows) {
      const says = [...one.querySelectorAll(":scope > [data-says] > p")].map((line) => line.textContent ?? "");
      const sentences = says.join(" ").split(/(?<=\.)\s+/).filter((sentence) => sentence !== "");
      expect([one.dataset.key, says.length > 0, sentences.length <= 3]).toEqual([one.dataset.key, true, true]);
      // Each holds something that is drawn, beside what is said of it.
      expect([one.dataset.key, one.querySelector(":scope > [data-drawn-here]")?.children.length ?? 0]).not.toEqual([one.dataset.key, 0]);
    }
  });
});

describe("the way to a part of the key", () => {
  const contents = () => within(key()).getByRole("navigation", { name: ABOUT.key.contents.label });
  const parts = () => within(key()).getAllByRole("heading", { level: 3 });

  test("test_the_key_opens_with_its_parts_by_name_so_that_a_drawing_is_found_without_reading_every_row", () => {
    // Measured on a phone, 390 by 844: the key was seven screens, and nothing at its head
    // said what it held. It opens with its parts, each by the name its part bears, so that
    // a person goes to the part where the drawing they met is, and reads that part alone.
    render(<Key meta={meta} />);
    const links = within(contents()).getAllByRole("link");

    expect(links).toHaveLength(5);
    // What is heard of a link, and read beside its drawings, is the name of its part and no more.
    links.forEach((link, at) => {
      expect(link).toHaveAccessibleName(parts()[at]?.textContent ?? "");
      expect(link.querySelector(":scope > :not([aria-hidden='true'])")?.textContent).toBe(parts()[at]?.textContent);
    });
    expect(links.map((link) => link.getAttribute("href"))).toEqual(parts().map((heading) => `#${heading.id}`));
    // Each part is found by a name that does not change as the page is built again.
    expect(parts().map((heading) => heading.id)).toEqual(["key-things", "key-steps", "key-result", "key-map", "key-town"]);
    // It stands after what the key says of itself, and before the first of its parts.
    const lead = within(key()).getByText(ABOUT.key.lead);
    expect(lead.compareDocumentPosition(contents()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(contents().compareDocumentPosition(parts()[0] as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // Each is a link of the size of a main control, and leads to a part of the same page.
    for (const link of links) {
      expect(link).toHaveClass("target");
      expect(link.getAttribute("href")?.startsWith("#")).toBe(true);
    }
  });

  test("test_each_part_is_shown_by_a_drawing_or_two_of_what_it_holds_which_say_nothing", () => {
    render(<Key meta={meta} />);
    const [first] = meta.tags;
    const shown = within(contents())
      .getAllByRole("link")
      .map((link) => link.querySelector<HTMLElement>(":scope > [aria-hidden='true']"));

    // The drawings are dress: the name beside them is what is read and heard. No word is
    // among them, seen or unseen: nothing but the number a pin bears, which is the first.
    expect(shown.map((one) => one?.textContent)).toEqual(["", "", "", "1", ""]);
    for (const one of shown) {
      expect(one).not.toBeNull();
      expect(one?.querySelectorAll("a, button, [tabindex], [role='img'], .visually-hidden")).toHaveLength(0);
    }
    const drawn = shown.map((one) => drawnIn(one as HTMLElement));
    // A vibe, a journey and a budget. The steps with their peg. A carrot, a flag and a key. A pin. A town.
    expect(drawn[0]).toEqual([
      pictured(drawingOf({ kind: "tag", id: first?.tag_id, family: first?.family })),
      pictured(drawingOf({ kind: "place" })),
      pictured(drawingOf({ kind: "budget" })),
    ]);
    expect(drawn[1]).toEqual([pictured("ui-peg")]);
    expect(drawn[2]).toEqual([pictured("ui-carrot"), pictured("ui-flag"), pictured("ui-key")]);
    expect(drawn[3]).toEqual([pictured("pin")]);
    expect(shown[3]?.querySelectorAll("[data-band], [data-pattern]")).toHaveLength(2);
    expect(drawn[4]?.length).toBeGreaterThan(3);
    expect(drawn[4]?.every((picture) => /\/art\/town-/.test(picture))).toBe(true);
    // Every drawing of it is one the part it leads to holds.
    const held = (id: string) => drawnIn(document.getElementById(id)?.closest("section") as HTMLElement);
    ["key-things", "key-steps", "key-result", "key-map", "key-town"].forEach((id, at) => {
      for (const picture of drawn[at] ?? []) expect([id, picture, held(id).includes(picture)]).toEqual([id, picture, true]);
    });
  });

  test("test_what_is_said_over_the_parts_says_how_many_there_are_and_what_a_press_does", () => {
    render(<Key meta={meta} />);

    expect(contents()).toHaveTextContent(ABOUT.key.contents.lead);
    expect(ABOUT.key.contents.lead).toMatch(/\bfive sections\b/);
    expect(ABOUT.key.contents.lead).toMatch(/Press a section to go straight to it\.$/);
    // What a vibe is worked out from was once called its parts. So the word is kept for a part
    // of a page or of a drawing where a list of such places names it, and is not said here.
    expect([ABOUT.key.contents.label, ABOUT.key.contents.lead].filter((words) => /\bparts?\b/i.test(words))).toEqual([]);
    expect(parts()).toHaveLength(5);
    // A release that holds no vibe has the same five parts.
    const none = render(<Key meta={{ ...meta, tags: [] }} />);
    expect(within(none.container).getAllByRole("heading", { level: 3 })).toHaveLength(5);
    expect(within(within(none.container).getByRole("navigation")).getAllByRole("link")).toHaveLength(5);
  });

  test("test_the_parts_stand_one_under_the_other_on_a_narrow_screen_and_side_by_side_where_there_is_room", () => {
    const list = setsOf(".parts");
    const link = setsOf(".parts a");

    expect(list.get("grid-template-columns")).toBe("repeat(auto-fill, minmax(min(100%, 19rem), 1fr))");
    // The drawings stand in a room of one width, so that the names begin on one line down the list.
    expect(link.get("grid-template-columns")).toBe("var(--shown) minmax(0, 1fr)");
    expect([setsOf(".toParts").get("--shown"), setsOf(".toParts", "@media (min-width: 60rem)").get("--shown")]).toEqual(["7.5rem", "11rem"]);
  });
});

describe("the things in a search, in the key", () => {
  test("test_every_vibe_of_the_release_has_its_drawing_beside_its_name_which_leads_to_the_vibe", () => {
    render(<Key meta={meta} />);

    const list = within(row("vibes")).getByRole("list", { name: ABOUT.key.things.vibesList });
    const links = within(list).getAllByRole("link");

    expect(saidBy("vibes")).toEqual([ABOUT.key.things.vibes]);
    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual(
      meta.tags.map((tag) => [tag.label, `#${tag.tag_id}`]),
    );
    meta.tags.forEach((tag, at) => {
      // By the id the service gives the vibe, then by its family, then the plain one. No vibe is named here.
      expect([tag.tag_id, drawnIn(links[at] as HTMLElement)]).toEqual([
        tag.tag_id,
        [pictured(drawingOf({ kind: "tag", id: tag.tag_id, family: tag.family }))],
      ]);
      // The drawing is dress: the link is named by the name of the vibe alone.
      expect(links[at]).toHaveAccessibleName(tag.label);
      expect(links[at]).toHaveClass("target-min");
    });
  });

  test("test_every_vibe_is_named_in_the_key_by_its_name_alone_and_none_is_said_to_be_less_sure", () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a user".
    // The service says which vibe is less sure, in a code, and no word more. One that is older
    // than the website, or later, may say its label and why: so both are laid on the release.
    const told = sayingSo(meta);
    render(<Key meta={told} />);

    expect(meta.tags.filter((tag) => tag.sureness === "rough_guide").map((tag) => tag.tag_id)).toEqual([ROUGH.tag_id]);
    expect(told.rough_guides).toEqual([ROUGH]);
    expect(key().querySelector("[data-rough-guide]")).toBeNull();
    const said = key().textContent ?? "";
    expect(said.length).toBeGreaterThan(500);
    expect([said.includes(ROUGH.label), said.includes(ROUGH.why), /less sure|rough guide/i.test(said)]).toEqual([false, false, false]);
    // Each name stands in its row with the drawing of its vibe, and nothing beside it.
    const named = [...row("vibes").querySelectorAll("ul > li")];
    expect(named.map((one) => [one.children.length, one.textContent])).toEqual(meta.tags.map((tag) => [1, tag.label]));
  });

  test("test_a_release_with_no_vibe_draws_none_and_says_nothing_of_one", () => {
    render(<Key meta={{ ...meta, tags: [] }} />);

    expect(key().querySelector("[data-key='vibes']")).toBeNull();
    expect(key().querySelector("[data-key='off']")).toBeNull();
    expect(key().querySelector("[data-key='scale']")).toBeNull();
    // What is no vibe is drawn as it was.
    expect(key().querySelector("[data-key='others']")).not.toBeNull();
  });

  test("test_the_other_things_a_person_can_ask_for_are_each_drawn_by_the_drawing_of_its_kind", () => {
    render(<Key meta={meta} />);

    const items = within(within(row("others")).getByRole("list", { name: ABOUT.key.things.othersList })).getAllByRole("listitem");

    expect(OTHER_THINGS).toEqual(["place", "budget", "tenure", "home", "area"]);
    expect(items.map((item) => [drawnIn(item), item.textContent])).toEqual(
      OTHER_THINGS.map((kind) => [[pictured(drawingOf({ kind }))], ABOUT.key.things.kinds[kind]]),
    );
    // The chip of the usual settings goes, and nothing draws a likeness: neither is in the key.
    const left: readonly ThingKind[] = ["usual", "alike"];
    for (const kind of left) expect(drawnIn(key())).not.toContain(pictured(drawingOf({ kind })));
  });

  test("test_a_thing_that_counts_for_nothing_is_shown_in_colour_and_in_outline_side_by_side", () => {
    render(<Key meta={meta} />);
    const first = meta.tags[0]!;
    const drawing = drawingOf({ kind: "tag", id: first.tag_id, family: first.family });

    expect(drawnIn(row("off"))).toEqual([pictured(drawing), pictured(`${drawing}-off` as Drawing)]);
    expect(saidBy("off")).toEqual([ABOUT.key.things.off]);
    // No edge of a thing is dashed here: what nobody said is said in words where it is met.
    expect(row("off").querySelector("[data-state='assumed']")).toBeNull();
  });

  test("test_how_much_a_thing_counts_is_the_gauge_of_the_settings_with_as_many_steps_and_at_their_size", () => {
    render(<Key meta={meta} />);

    const cells = (name: string) => row(name).querySelectorAll("[data-full]");
    const full = (name: string) => row(name).querySelectorAll("[data-full='true']");

    expect([cells("gauge").length, full("gauge").length]).toEqual([STEPS, 6]);
    // Of a scale, as many steps run each way from the middle as the settings draw.
    expect([cells("gauge-of-a-scale").length, full("gauge-of-a-scale").length]).toEqual([eachWay(STEPS) * 2, 3]);
    // It is drawn and says nothing: the sentence beside it says what it is.
    for (const name of ["gauge", "gauge-of-a-scale"]) {
      expect(row(name).querySelector("[data-drawn-here]")?.textContent).toBe("");
      expect(row(name).querySelector("[data-alone='false']")).not.toBeNull();
    }
    expect([saidBy("gauge"), saidBy("gauge-of-a-scale")]).toEqual([[ABOUT.key.things.gauge], [ABOUT.key.things.gaugeOfAScale]]);
    // The settings draw at the small pixel on every screen, and so does the key.
    expect(setsOf('.key [data-key^="gauge"] > [data-drawn-here]').get("--px")).toBe("var(--px-small)");
  });

  test.each([
    ["cross", "ui-cross", ABOUT.key.things.cross],
    ["carrot", "ui-carrot", ABOUT.key.result.carrot],
    ["arrow", "ui-arrow", ABOUT.key.result.arrow],
  ] as const)("test_a_small_mark_is_drawn_once_beside_what_it_means_and_says_nothing: %s", (name, drawing, says) => {
    render(<Key meta={meta} />);

    const drawn = [...row(name).querySelectorAll<HTMLElement>("[style*='/art/']")];

    expect(drawn.map((one) => one.style.getPropertyValue("--art"))).toEqual([pictured(drawing)]);
    expect(drawn[0]?.closest("[aria-hidden='true']")).not.toBeNull();
    expect(saidBy(name)).toEqual([says]);
  });

  test("test_the_arrow_points_down_as_the_arrow_of_a_fold_that_is_closed_does", () => {
    // The drawing points up, and a fold turns it to point at what is closed.
    expect(setsOf('.key [data-key="arrow"] > [data-drawn-here] > *').get("transform")).toBe("rotate(180deg)");
  });

  test("test_the_rank_is_the_pennant_of_a_result_and_the_source_is_the_key_which_opens_nothing_here", () => {
    render(<Key meta={meta} />);

    expect(drawnIn(row("rank"))).toEqual([pictured("ui-flag")]);
    expect(row("rank").querySelector("[data-drawn-here]")?.textContent).toContain("1");
    // It is of no result, and says no rank to whoever hears the page.
    expect(row("rank").querySelector("[data-drawn-here] > *")).toHaveAttribute("aria-hidden", "true");
    expect(saidBy("rank")).toEqual([ABOUT.key.result.rank]);
    expect(drawnIn(row("source"))).toEqual([pictured("ui-key")]);
    // It is the drawing alone, and is no button: a key that opened nothing would be a key that is broken.
    expect(row("source").querySelector("[data-drawn-here]")?.textContent).toBe("");
    expect(row("source").querySelectorAll("button, a, summary")).toHaveLength(0);
    expect(saidBy("source")).toEqual([ABOUT.key.result.source]);
  });
});

describe("what was drawn since the key was first made, in the key", () => {
  test("test_every_group_the_things_of_a_search_are_gathered_in_has_the_drawing_of_its_bar_beside_its_name", () => {
    render(<Key meta={meta} />);

    const items = within(within(row("groups")).getByRole("list", { name: ABOUT.key.things.groupsList })).getAllByRole("listitem");
    // The groups of the settings, as a search starts, but for those of a person's own
    // choices, which stand in the key as the things of a search.
    const ofChoices = ["money", "journeys", "hidden"];
    const groups = groupsOf(meta.defaults.rent, meta, [], {}).filter((group) => !ofChoices.includes(group.key));
    const ofAFamily = groups.filter((group) => group.key.startsWith("family:"));

    expect(saidBy("groups")).toEqual([ABOUT.key.things.groups]);
    // One for each family of vibes, and the three of no family, which had no drawing of their own.
    expect([ofAFamily.length, groups.length - ofAFamily.length]).toEqual([meta.families.length, 3]);
    expect(items.map((item) => [drawnIn(item), item.textContent])).toEqual(
      groups.map((group) => [[pictured(drawingOf(group.thing))], group.label]),
    );
    // Each has a drawing of its own: none is left under the plain box, and no two are drawn alike.
    const drawn = items.flatMap((item) => drawnIn(item));
    expect(drawn).not.toContain(pictured(PLAIN));
    expect(new Set(drawn).size).toBe(drawn.length);
    // The drawing is dress, and the name is read: nothing of a group is pressed here.
    for (const item of items) {
      expect(item.querySelector("[style*='/art/']")?.closest("[aria-hidden='true']")).not.toBeNull();
      expect(item.querySelectorAll("a, button")).toHaveLength(0);
    }
  });

  test.each(TRADE_OFF_MAY_BE_SHOWN)("test_what_stands_beside_a_trade_off_is_in_the_key_and_is_said_to_be_what_it_is_drawn_as: %s", (shown) => {
    render(<Key meta={meta} tradeOff={shown} />);
    const drawing = { scales: "ui-tradeoff", arrows: "ui-tradeoff-b" } as const;

    expect(drawnIn(row("trade-off"))).toEqual([pictured(drawing[shown])]);
    expect(row("trade-off").querySelector("[style*='/art/']")?.closest("[aria-hidden='true']")).not.toBeNull();
    expect(saidBy("trade-off")).toEqual([ABOUT.key.result.tradeOff[shown]]);
    // It says what is drawn, and the other way of drawing one is not in the key.
    expect(ABOUT.key.result.tradeOff[shown]).toMatch(shown === "scales" ? /^A pair of scales\b/ : /^Two arrows\b/);
    const other = drawing[shown === "scales" ? "arrows" : "scales"];
    expect(drawnIn(key())).not.toContain(pictured(other));
  });

  test("test_a_trade_off_is_what_a_person_would_give_up_and_nothing_of_it_warns_or_gives_a_verdict", () => {
    expect(TRADE_OFF_MAY_BE_SHOWN).toContain(TRADE_OFF_SHOWN);
    for (const says of Object.values(ABOUT.key.result.tradeOff)) {
      expect(says).toMatch(/what you would give up in return for the rest/);
      expect(/\b(bad|badly|worse|worst|fault|warning|danger|red)\b/i.test(says)).toBe(false);
    }
    // The arrow that stood beside a trade-off is gone from every result, and is in no row of the key.
    render(<Key meta={meta} />);
    expect(row("arrow").textContent?.includes("trade")).toBe(false);
  });

  test("test_the_mark_of_what_is_not_whole_is_in_the_key_with_its_two_words", () => {
    render(<Key meta={meta} />);

    expect(drawnIn(row("part"))).toContain(pictured("ui-approx"));
    expect(saidBy("part")).toEqual([ABOUT.band.states.part]);
    // It is drawn once in the key, in the row that says what it means.
    expect(drawnIn(key()).filter((picture) => picture === pictured("ui-approx"))).toHaveLength(1);
  });
});

describe("what Burro does with a sentence, in the key", () => {
  test("test_nothing_of_the_key_speaks_of_a_question_or_of_a_choice_that_burro_waits_for", () => {
    // The key said that Burro asks when it is not sure, and adds nothing until a person
    // chooses. Burro takes what it read and asks nothing.
    render(<Key meta={meta} />);
    const said = key().textContent ?? "";

    expect(/\bquestion\b|\bBurro asks\b|\buntil you choose\b|\badds nothing\b/i.test(said)).toBe(false);
    expect(said.includes(ABOUT.key.things.cross)).toBe(true);
    expect(said.includes(ABOUT.key.result.never)).toBe(true);
  });

  test("test_the_carrot_is_in_the_key_for_as_long_as_a_list_draws_it_beside_the_choice_in_hand", () => {
    // The examples and the places that match each lay it beside the one in hand.
    const sheets = ["../PromptBox/PromptBox.module.css", "../PlaceCombobox/PlaceCombobox.module.css"].map((file) =>
      readFileSync(path.resolve(__dirname, file), "utf8"),
    );

    for (const sheet of sheets) expect(sheet.includes("var(--carrot)")).toBe(true);
    render(<Key meta={meta} />);
    expect(drawnIn(row("carrot"))).toEqual([pictured("ui-carrot")]);
  });
});

describe("the rabbit, of whom the key draws nothing", () => {
  test("test_no_row_of_the_key_is_of_the_rabbit_and_nothing_of_him_is_drawn_or_said_in_it", () => {
    // A button stood by him, with a mark and no word, and the key said what its two marks
    // were. The button is gone, and its row with it. He is no mark to be explained, and
    // brown is his alone: so nothing of him is in the key.
    render(<Key meta={meta} />);

    expect(key().querySelector("[data-key='rabbit']")).toBeNull();
    expect(drawnIn(key()).filter((picture) => /burro/.test(picture))).toEqual([]);
    expect(/\brabbit\b|\bstops? him\b|\bmove again\b/i.test(key().textContent ?? "")).toBe(false);
    expect(Object.keys(ABOUT.key.result)).toEqual(["title", "carrot", "rank", "source", "tradeOff", "arrow", "notice", "never", "fault"]);
    // Nothing of the key is pressed but the way to a part of it and the name of a vibe.
    expect(key().querySelectorAll("button, input, [tabindex]")).toHaveLength(0);
  });

  test("test_the_part_of_what_is_met_on_every_page_is_named_for_a_result_and_for_the_whole_of_the_website", () => {
    // A key of a source, an arrow and a note are met on every page, and the part was named
    // for a search and a result alone.
    expect(ABOUT.key.result.title).toBe("On a result and across Burro");
    expect(new Set([ABOUT.key.things.title, ABOUT.band.title, ABOUT.key.result.title, ABOUT.key.map.title, TOWN.key.title]).size).toBe(5);
  });
});

describe("a note and a fault, in the key", () => {
  test("test_a_band_of_amber_is_a_note_and_a_band_of_poppy_is_a_fault_each_drawn_as_the_website_draws_one", () => {
    render(<Key meta={meta} />);

    expect(row("notice").querySelector("[data-edge='notice']")).toHaveAttribute("aria-hidden", "true");
    expect(row("fault").querySelector("[data-edge='fault']")).toHaveAttribute("aria-hidden", "true");
    // Under what a note is: the two kinds of thing that Burro leaves out of a search unless a person chooses them.
    expect([saidBy("notice"), saidBy("fault")]).toEqual([
      [ABOUT.key.result.notice, ABOUT.key.result.never],
      [ABOUT.key.result.fault],
    ]);
    // Cream inside a rule of ink, with the band inside the rule: the colour is a mark, and never the colour of words.
    const slip = setsOf(".noteEdge");
    expect([slip.get("background-color"), slip.get("border")]).toEqual(["var(--notice-bg)", "var(--edge) solid var(--notice-edge)"]);
    expect(setsOf('.noteEdge[data-edge="notice"]').get("box-shadow")).toBe("inset calc(var(--px) * 2) 0 0 var(--notice-mark)");
    expect(setsOf('.noteEdge[data-edge="fault"]').get("box-shadow")).toBe("inset calc(var(--px) * 2) 0 0 var(--error-edge)");
    expect(RULES.filter((rule) => /var\(--(amber|poppy|notice-mark|error-edge)\)/.test(rule.sets.get("color") ?? ""))).toEqual([]);
  });

  test("test_what_is_said_of_them_says_what_the_colour_marks_and_names_no_verdict", () => {
    // What a note may be of is said by an example that every page bears out, and by none that is gone.
    expect(ABOUT.key.result.notice).toContain("a note that Burro wants you to read");
    expect(ABOUT.key.result.notice).toContain("the line that names what it left out of your search");
    expect(/less sure|rough guide/i.test(JSON.stringify(ABOUT))).toBe(false);
    expect(ABOUT.key.result.fault).toContain("something that went wrong");
    expect(/\b(safe|unsafe|dangerous|rough)\b/i.test(JSON.stringify(ABOUT))).toBe(false);
  });
});

describe("the map, in the key", () => {
  test("test_a_pin_is_the_drawing_of_the_map_with_the_number_of_the_first_on_it", () => {
    render(<Key meta={meta} />);

    expect(drawnIn(row("pin"))).toEqual([pictured("pin")]);
    expect(row("pin").querySelector("[data-drawn-here]")?.textContent).toBe("1");
    expect(row("pin").querySelector("[data-drawn-here] > *")).toHaveAttribute("aria-hidden", "true");
    expect(saidBy("pin")).toEqual([ABOUT.key.map.pin]);
    // How many results bear a pin is the map's to say.
    expect(PINS).toBe(10);
    expect(ABOUT.key.map.pin).toContain("the first ten results");
  });

  test("test_the_five_shades_of_green_are_the_five_colours_of_the_map_from_the_palest_to_the_darkest", () => {
    render(<Key meta={meta} />);

    const shades = [...row("greens").querySelectorAll<HTMLElement>("[data-band]")];

    expect(shades.map((one) => one.dataset.band)).toEqual(["1", "2", "3", "4", "5"]);
    for (const band of [1, 2, 3, 4, 5]) {
      expect(setsOf(`.swatch[data-band="${band}"]`).get("background-color")).toBe(`var(--map-${band})`);
    }
    expect(row("greens").querySelector("[data-drawn-here] > *")).toHaveAttribute("aria-hidden", "true");
    expect(saidBy("greens")).toEqual([ABOUT.key.map.greens]);
    expect(ABOUT.key.map.greens).toContain("five shades of green");
  });

  test("test_land_with_no_match_dots_lines_and_water_are_each_drawn_as_the_map_draws_them", () => {
    render(<Key meta={meta} />);

    expect(row("sand").querySelector("[data-band='0']")).not.toBeNull();
    expect(setsOf(".swatch").get("background-color")).toBe("var(--map-land)");
    expect(row("dots").querySelector("[data-pattern='unranked']")).not.toBeNull();
    expect(row("lines").querySelector("[data-pattern='filtered']")).not.toBeNull();
    expect(row("water").querySelector("[data-water]")).not.toBeNull();
    expect(setsOf(".swatch[data-water]").get("background-color")).toBe("var(--map-water)");
    expect([saidBy("sand"), saidBy("dots"), saidBy("lines"), saidBy("water")]).toEqual([
      [ABOUT.key.map.sand],
      [ABOUT.key.map.dots],
      [ABOUT.key.map.lines],
      [ABOUT.key.map.water],
    ]);
  });

  test("test_what_is_drawn_of_the_map_is_at_the_pixel_of_the_map", () => {
    const tokens = asWritten();

    // A pixel of the map is a pixel of the ground, on every screen.
    expect(setsOf(".swatch").get("--px-map")).toBe("var(--px-ground)");
    expect(setsOf(".drawnPin").get("--px-map")).toBe("var(--px-ground)");
    expect(tokens["--px-ground"]).toBe("2px");
    expect(setsOf(".swatch").get("border")).toBe("var(--px-map) solid var(--map-line)");
  });
});

describe("the key, in the look", () => {
  test("test_no_edge_of_the_key_is_dashed_and_every_colour_is_a_token", () => {
    for (const sheet of SHEETS) {
      const written = sheet.replace(/\/\*[\s\S]*?\*\//g, "");
      expect(/\b(dashed|dotted)\b/.test(written)).toBe(false);
      expect(written.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl)a?\(/gi) ?? []).toEqual([]);
    }
  });

  test("test_a_drawing_is_shown_at_its_own_size_and_never_stretched", () => {
    // What lays a drawing out sets where it stands. Its size is its own, in art pixels.
    const stretched = RULES.filter((rule) => /\.drawn\b|data-drawn-here/.test(rule.selector)).flatMap((rule) =>
      [...rule.sets.keys()]
        // The arrow is turned, as the arrow of a fold is, and is of the size it was.
        .filter((property) => /^(width|height|transform|zoom|scale)$/.test(property) && !/data-key="arrow"/.test(rule.selector))
        .map((property) => `${rule.selector} sets ${property}`),
    );

    expect(stretched).toEqual([]);
    expect(RULES.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition)/.test(property)))).toEqual([]);
  });

  test("test_the_room_of_a_drawing_is_as_wide_as_the_widest_drawing_of_its_group_so_that_none_lies_over_its_sentence", () => {
    // Seen in a browser at 1440 by 900: a scale with the picture of each of its ends is 372
    // pixels wide, and in a room of 248 it lay over the sentence beside it. A gauge with the
    // picture of each of its ends is 261, and has where the area sits in words beside it.
    render(<Key meta={meta} />);
    const room = (selector: string) => setsOf(selector).get("--drawn-wide");
    const groups = [...key().querySelectorAll<HTMLElement>("section")].map((one) => [one.querySelector("h3")?.textContent, one.dataset.lay]);

    expect(groups).toEqual([
      [ABOUT.key.things.title, "pairs"],
      // The steps are wide, and what is said of each is long: one row to a line.
      [ABOUT.band.title, "lines"],
      [ABOUT.key.result.title, "pairs"],
      [ABOUT.key.map.title, "pairs"],
      [TOWN.key.title, "pairs"],
    ]);
    expect([room(".things"), room(".steps"), room(".towns")]).toEqual([undefined, "27rem", "15.5rem"]);
    expect(setsOf(".ofThings").get("--drawn-wide")).toBe("10rem");
    // What a group is given outweighs what every group has, whichever sheet is read last.
    expect(RULES.filter((rule) => rule.sets.has("--drawn-wide")).map((rule) => rule.selector).sort()).toEqual(
      [".ofThings", ".steps", ".towns", ":where(.group)"].sort(),
    );
  });

  test("test_a_small_drawing_stands_beside_its_sentence_and_a_wide_one_over_it_on_a_narrow_screen", () => {
    const small = setsOf('.row[data-drawn="small"]');
    const wide = setsOf('.row[data-drawn="wide"]', "@media (min-width: 40rem)");

    expect(small.get("grid-template-columns")).toBe("var(--drawn-small) minmax(0, 1fr)");
    expect(setsOf('.row[data-drawn="wide"]').get("grid-template-columns")).toBe("minmax(0, 1fr)");
    expect(wide.get("grid-template-columns")).toBe("var(--drawn-wide) minmax(0, 1fr)");
  });

  test("test_nothing_of_the_key_moves_and_nothing_can_be_pressed_but_the_way_to_a_part_and_the_name_of_a_vibe", () => {
    render(<Key meta={meta} />);

    const pressed = [...key().querySelectorAll("a, button, input, select, textarea, summary, [tabindex]")];

    // The five parts of the key, and then every vibe: each is a link to a place on the same page.
    expect(pressed.map((one) => one.tagName)).toEqual([...Array.from({ length: 5 }, () => "A"), ...meta.tags.map(() => "A")]);
    expect(pressed.filter((one) => !(one.getAttribute("href") ?? "").startsWith("#"))).toEqual([]);
    expect(RULES.filter((rule) => /:(hover|focus|active)/.test(rule.selector))).toEqual([]);
  });

  test("test_the_key_gives_no_verdict_and_says_that_more_is_not_better", () => {
    const said = JSON.stringify([ABOUT.key, ABOUT.band, TOWN.key]);

    expect(/%|percent|\bscore|\bbest\b|\bworst\b|\bwin\b|\bprize|\bstars?\b|!/i.test(said)).toBe(false);
    expect(ABOUT.band.lead).toContain("and not that the area is better");
    expect(ABOUT.key.result.rank).toContain("has not won anything");
  });

  test.each([
    ["the made-up city", meta],
    ["a preview", preview],
    ["a release that holds no recorded crime", variantA],
  ])("test_it_has_no_accessibility_fault: %s", async (_, given) => {
    const { container } = render(
      <main>
        <h1>Vibes</h1>
        <Key meta={given} />
      </main>,
    );

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});
