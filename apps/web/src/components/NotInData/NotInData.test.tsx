import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { NOT_IN_DATA } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import { paths } from "@/lib/paths";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { isDrawn, sizeOf } from "../kit/drawings";
import { PLAIN } from "../kit/Thing/drawn";
import { NotInData } from "./NotInData";

type Missing = Parameters<typeof NotInData>[0]["missing"];

const form = recordedAnswer("get_meta", "preview/meta").body.data;
/** One vibe that no area is placed on, as the service named it. */
const one: Missing = recordedAnswer("interpret", "preview/interpret-plain").body.data.not_in_release;
/** A measure, a journey and a budget, in that order, as the service named them. */
const three: Missing = recordedAnswer("interpret", "preview/interpret-long").body.data.not_in_release;
const [vibe] = one;
const [measure, journey, budget] = three;
if (!vibe || !measure || !journey || !budget) throw new Error("the recordings name nothing as missing");
const idOf = (target: string) => target.slice(target.indexOf(":") + 1);

const ALL = rulesOf(readFileSync(path.join(__dirname, "NotInData.module.css"), "utf8"));
const STYLES = ALL.filter((rule) => rule.under === null);
const setsOf = (selector: string, rules = STYLES) =>
  new Map(rules.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

const notice = () => screen.getByRole("status", { name: NOT_IN_DATA.title });
const line = () => notice().querySelector("summary") as HTMLElement;
/** The drawing that stands beside each thing, by the name of its picture. */
const drawn = () =>
  within(notice())
    .getAllByRole("listitem")
    .map(
      (item) =>
        /\/art\/([a-z0-9-]+)\.png/.exec(item.querySelector<HTMLElement>("[style]")?.style.getPropertyValue("--art") ?? "")?.[1],
    );
/** A drawing in outline, which is what is drawn of a thing that counts for nothing. */
const inOutline = (drawing: string) => `${drawing}-off`;

describe("what was asked for and is not in the data", () => {
  test("test_the_recordings_name_a_vibe_a_measure_a_journey_and_a_budget", () => {
    expect([vibe.target.startsWith("tag:"), measure.target.startsWith("feature:")]).toEqual([true, true]);
    expect([journey.target, budget.target]).toEqual(["commute", "budget"]);
    // The label the service gives a budget holds the amount that was typed.
    expect(/\d/.test(budget.label)).toBe(true);
  });

  test("test_with_nothing_missing_nothing_is_on_the_page", () => {
    const { container } = render(<NotInData missing={[]} meta={form} />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_it_names_each_thing_in_one_line_that_is_closed_and_opens_by_the_browsers_own_element", async () => {
    const user = userEvent.setup({ delay: null });
    render(<NotInData missing={three} meta={form} />);
    const opens = notice().querySelector("details") as HTMLDetailsElement;

    expect(opens.open).toBe(false);
    expect(line().textContent).toBe(
      `${NOT_IN_DATA.title}: ${[measure.label, NOT_IN_DATA.commute, NOT_IN_DATA.budget].join("; ")}`,
    );
    expect(line()).toHaveClass("target-min");
    // The notice holds what opens and nothing beside it: nothing of it is said twice.
    expect(notice().querySelectorAll(":scope > :not(details)")).toHaveLength(0);

    await user.click(line());
    expect(opens.open).toBe(true);
  });

  test("test_what_it_opens_to_says_how_many_things_and_of_each_its_name_and_why", () => {
    render(<NotInData missing={three} meta={form} />);
    const said = [...(notice().querySelector("details")?.children ?? [])].filter((child) => child !== line());
    const things = within(notice()).getAllByRole("listitem");

    expect(said).toHaveLength(1);
    expect(said[0]?.querySelector("p")?.textContent).toBe(NOT_IN_DATA.lead(3));
    expect(things.map((thing) => thing.textContent)).toEqual([
      `${measure.label}. ${NOT_IN_DATA.why.feature}`,
      `${NOT_IN_DATA.commute}. ${NOT_IN_DATA.why.commute}`,
      `${NOT_IN_DATA.budget}. ${NOT_IN_DATA.why.budget}`,
    ]);
    expect(things.map((thing) => thing.querySelector("strong")?.textContent)).toEqual([
      measure.label,
      NOT_IN_DATA.commute,
      NOT_IN_DATA.budget,
    ]);
  });

  test("test_a_vibe_says_what_it_waits_on_in_the_services_words_and_leads_to_what_each_vibe_waits_on", () => {
    render(<NotInData missing={one} meta={form} />);
    const waits = form.recipes.find((held) => held.tag_id === idOf(vibe.target))?.waits_on ?? [];
    const [thing] = within(notice()).getAllByRole("listitem");

    expect(waits.length).toBeGreaterThan(0);
    expect(thing?.textContent).toBe(
      `${vibe.label}. ${NOT_IN_DATA.why.vibe} ${NOT_IN_DATA.waitsOn(
        waits.map((part) => NOT_IN_DATA.part(part.label, part.hundredths)).join("; "),
      )}`,
    );
    const more = within(notice()).getByRole("link", { name: NOT_IN_DATA.more });
    expect(more).toHaveAttribute("href", paths.vibes());
    expect(more).toHaveClass("target-min");
  });

  test("test_where_no_vibe_is_missing_there_is_no_link_to_the_vibes", () => {
    render(<NotInData missing={three} meta={form} />);

    expect(within(notice()).queryByRole("link")).toBeNull();
  });

  test("test_a_budget_and_a_journey_are_named_by_the_page_and_never_by_a_label_that_may_hold_what_was_typed", () => {
    const CANARY = "zqxcanary7431";
    render(
      <NotInData
        missing={[
          { target: "budget", label: `${budget.label} ${CANARY}` },
          { target: "commute", label: `${journey.label} ${CANARY}` },
        ]}
        meta={form}
      />,
    );

    expect(document.body.innerHTML.includes(CANARY)).toBe(false);
    // Nor the amount, which the label of the recording holds.
    const amount = /\d[\d,.]*/.exec(budget.label)?.[0] ?? "no amount";
    expect(budget.label.includes(amount)).toBe(true);
    expect(document.body.innerHTML.includes(amount)).toBe(false);
  });

  test("test_each_thing_is_drawn_in_outline_because_it_counts_for_nothing", () => {
    const [first] = form.tags;
    const unplaced = form.features.find((feature) => feature.family === null);
    const placed = form.features.find((feature) => feature.family !== null);
    if (!first || !unplaced || !placed) throw new Error("the recorded form holds too little");
    render(
      <NotInData
        missing={[
          ...three,
          vibe,
          // A vibe that nobody has drawn yet is drawn by the family the service puts it in.
          { target: "tag:not_yet_drawn", label: "A vibe nobody has drawn" },
          // A measure is drawn by its family, and one whose family the service does not name is drawn plain.
          { target: `feature:${placed.feature_id}`, label: placed.label },
          { target: `feature:${unplaced.feature_id}`, label: unplaced.label },
        ]}
        meta={{ ...form, tags: [...form.tags, { ...first, tag_id: "not_yet_drawn" as never }] }}
      />,
    );

    const ofTheVibe = `thing-${idOf(vibe.target).replaceAll("_", "-")}`;
    expect([isDrawn(ofTheVibe), isDrawn("thing-not-yet-drawn")]).toEqual([true, false]);
    expect(drawn()).toEqual([
      // The measure of the recording is one the preview does not hold, so the form names no family for it.
      inOutline(PLAIN),
      inOutline("thing-journey"),
      inOutline("thing-budget"),
      inOutline(ofTheVibe),
      inOutline(`thing-family-${first.family.replaceAll("_", "-")}`),
      inOutline(`thing-family-${(placed.family ?? "").replaceAll("_", "-")}`),
      inOutline(PLAIN),
    ]);
    for (const name of drawn()) expect([name, isDrawn(name ?? "")]).toEqual([name, true]);
    // A drawing is dress. It says nothing to whoever hears the page: the name beside it does.
    for (const item of within(notice()).getAllByRole("listitem")) {
      expect(item.querySelector("[style]")?.closest("[aria-hidden='true']")).not.toBeNull();
      expect(item.querySelector("[role='img']")).toBeNull();
    }
  });

  test("test_it_is_drawn_where_the_page_hands_it_what_is_held_of_each_recipe_and_no_more", () => {
    render(<NotInData missing={[...one, ...three]} meta={{ recipes: form.recipes }} />);

    expect(drawn()).toEqual([
      inOutline(`thing-${idOf(vibe.target).replaceAll("_", "-")}`),
      inOutline(PLAIN),
      inOutline("thing-journey"),
      inOutline("thing-budget"),
    ]);
  });

  test("test_the_mark_of_the_line_is_the_arrow_of_the_look_and_says_nothing", () => {
    render(<NotInData missing={one} meta={form} />);
    const mark = line().querySelector<HTMLElement>("[style]");
    const { width, height } = sizeOf("ui-arrow");

    expect(mark?.style.getPropertyValue("--art")).toBe('url("/art/ui-arrow.png")');
    expect([mark?.style.getPropertyValue("--w"), mark?.style.getPropertyValue("--h")]).toEqual([String(width), String(height)]);
    expect(mark).toHaveAttribute("aria-hidden", "true");
    expect(mark?.textContent).toBe("");
    // The arrow is drawn pointing up. Closed, it points at the line. Open, it points down at what the line opened.
    expect(setsOf(".opens > summary > .mark").get("transform")).toBe("rotate(90deg)");
    expect(setsOf(".opens[open] > summary > .mark").get("transform")).toBe("rotate(180deg)");
    // Turned, it takes the room it took: a square as wide as the arrow is long.
    expect([setsOf(".mark").get("width"), setsOf(".mark").get("height")]).toEqual([
      `calc(var(--px) * ${Math.max(width, height)})`,
      `calc(var(--px) * ${Math.max(width, height)})`,
    ]);
    // It stands beside the first line of the words, however many lines they run to.
    expect(setsOf(".opens > summary").get("align-items")).toBe("start");
    expect(setsOf(".mark").get("margin-block-start")).toBe("calc((var(--leading-text) * 1em - var(--px) * 10) / 2)");
    // It does not turn as the pointer or the focus comes or goes, and it takes no time to turn.
    expect(ALL.filter((rule) => /:(hover|focus|active)/.test(rule.selector))).toEqual([]);
    expect(ALL.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition)/.test(property)))).toEqual([]);
  });

  test("test_it_is_a_notice_cream_with_a_band_of_amber_inside_a_rule_of_ink_and_flat", () => {
    render(<NotInData missing={one} meta={form} />);

    // The frame of the kit brings the cream and the rule of ink. It is the plain one: a notice throws no shadow.
    expect(notice()).toHaveClass("frame", "plain", "missing");
    expect(notice()).not.toHaveClass("roomy");
    expect(setsOf(".missing").get("box-shadow")).toBe("inset calc(var(--px) * 2) 0 0 var(--notice-mark)");
    expect(STYLES.filter((rule) => rule.sets.has("background") || rule.sets.has("background-color")).map((rule) => rule.selector)).toEqual([]);
    // What is read stands clear of the band.
    expect(setsOf(".opens > summary").get("padding-inline-start")).toBe("calc(var(--px) * 5)");
    expect(setsOf(".why").get("padding-inline-start")).toBe("calc(var(--px) * 5)");
  });

  test("test_why_stands_under_a_solid_rule_of_ink_and_no_edge_of_it_is_in_dashes_or_in_dots", () => {
    // A person who walked the website did not know what a dashed edge was for.
    const written = readFileSync(path.join(__dirname, "NotInData.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

    expect(/dashed|dotted|repeating-linear-gradient/.test(written)).toBe(false);
    expect(setsOf(".why").get("border-block-start")).toBe("var(--edge) solid var(--border)");
    expect(ALL.filter((rule) => rule.sets.has("border-style") || rule.sets.has("border-block-start-style")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_its_title_is_a_short_label_in_the_face_of_names_and_the_rest_is_read", () => {
    expect(setsOf(".title").get("font")).toBe("400 var(--name-1) / 1 var(--font-name)");
    expect(setsOf(".title").get("font-synthesis")).toBe("none");
    // Every name, every sentence and every figure of it is set in the reading face, in ink.
    const faces = STYLES.filter((rule) => rule.selector !== ".title" && [...rule.sets.keys()].some((property) => /^font(-family)?$/.test(property)));
    expect(faces.map((rule) => rule.selector)).toEqual([]);
    expect(STYLES.filter((rule) => rule.sets.has("color")).map((rule) => [rule.selector, rule.sets.get("color")])).toEqual([
      [".missing", "var(--notice-text)"],
    ]);
  });

  test("test_it_has_no_accessibility_fault_closed_or_open", async () => {
    const user = userEvent.setup({ delay: null });
    const { container } = render(<NotInData missing={[...one, ...three]} meta={form} />);

    expect(await faultsIn(container)).toEqual([]);
    await user.click(line());
    expect(await faultsIn(container)).toEqual([]);
  });
});
