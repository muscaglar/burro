import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FILTERED, NOTHING_MATCHES, UNRANKED } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { faultsIn } from "../../../test/support/axe";
import { problemsWith } from "../../../test/support/contract";
import { rulesOf } from "../../../test/support/css";
import { NothingMatches, waysOut } from "./NothingMatches";

const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const nothing = recordedAnswer("rank", "rank-nothing-matches").body.data;
const meta = recordedAnswer("get_meta", "meta").body.data;
const NAMES = { "syn-p0021": "Cindermoor Works" };

const ALL = rulesOf(readFileSync(path.join(__dirname, "NothingMatches.module.css"), "utf8"));
const STYLES = ALL.filter((rule) => rule.under === null);
const setsOf = (selector: string, rules = STYLES) =>
  new Map(rules.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

function show(spec: PreferenceSpec = nothing.spec) {
  const sent: Operations[] = [];
  const view = render(
    <NothingMatches
      filtered={nothing.filtered}
      unranked={nothing.unranked}
      spec={spec}
      areas={areas}
      placeNames={NAMES}
      onEdit={(operations) => sent.push(operations)}
    />,
  );
  return { sent, user: userEvent.setup({ delay: null }), ...view };
}

describe("where a budget to rent was held against rents of a wider place", () => {
  const let_ = recordedAnswer("get_meta", "let/meta").body.data;

  function shown(spec: PreferenceSpec, form: typeof meta | undefined = let_) {
    return render(
      <NothingMatches
        filtered={nothing.filtered}
        unranked={nothing.unranked}
        spec={spec}
        areas={areas}
        placeNames={NAMES}
        meta={form}
        onEdit={() => undefined}
      />,
    );
  }

  test("test_the_count_of_what_was_left_out_says_which_places_the_rents_are_of", () => {
    shown({ ...nothing.spec, tenure: "rent" });

    expect(let_.rents?.of_a_place).toBeTruthy();
    expect(screen.getByText(let_.rents?.of_a_place ?? "no words")).toBeInTheDocument();
  });

  test("test_it_is_not_said_to_a_buyer_or_of_rents_that_are_of_the_area_alone", () => {
    const { unmount } = shown({ ...nothing.spec, tenure: "buy" });
    expect(screen.queryByText(let_.rents?.of_a_place ?? "no words")).toBeNull();
    unmount();

    shown({ ...nothing.spec, tenure: "rent" }, meta);
    expect(screen.queryByText(let_.rents?.of_a_place ?? "no words")).toBeNull();
  });
});

describe("when no area passes every limit", () => {
  test("test_the_page_says_so_and_counts_the_areas_left_out_for_each_reason", () => {
    show();

    const block = within(screen.getByRole("region", { name: NOTHING_MATCHES.title }));
    const counts = block.getAllByRole("term").map((term) => [term.textContent, term.nextElementSibling?.textContent]);
    expect(counts).toEqual([
      [FILTERED.over_budget, "21 areas"],
      [FILTERED.commute_cap, "1 area"],
      [UNRANKED.not_rankable, "2 areas"],
    ]);
    // Every area of the release is counted once.
    expect(21 + 1 + 2).toBe(areas.length);
  });

  test("test_an_area_left_out_by_an_estimate_is_counted_under_words_that_say_it_is_one", () => {
    // A release that holds no journey time: a firm limit leaves out what is likely beyond it.
    const firm = recordedAnswer("rank", "estimate/rank-firm").body.data;
    render(
      <NothingMatches
        filtered={firm.filtered}
        unranked={[]}
        spec={firm.spec}
        areas={areas}
        placeNames={NAMES}
        onEdit={() => undefined}
      />,
    );

    const block = within(screen.getByRole("region", { name: NOTHING_MATCHES.title }));
    const counts = block.getAllByRole("term").map((term) => [term.textContent, term.nextElementSibling?.textContent]);
    expect(new Set(firm.filtered.map((one) => one.reason))).toEqual(new Set(["commute_likely_beyond"]));
    expect(counts).toEqual([[FILTERED.commute_likely_beyond, NOTHING_MATCHES.count(firm.filtered.length)]]);
    // It ends in the line the service says of an estimate, as it was recorded.
    expect(FILTERED.commute_likely_beyond).toContain(recordedAnswer("get_meta", "estimate/meta").body.data.journey_estimate?.said ?? "no line");
    // The way out is the one for any firm limit on a journey: make it flexible.
    expect(screen.getAllByRole("button").map((button) => button.textContent)).toEqual([
      NOTHING_MATCHES.journeyFlexible("Cindermoor Works"),
    ]);
  });

  test("test_there_is_one_button_for_each_firm_limit_in_the_spec", () => {
    show();

    expect(screen.getAllByRole("button").map((button) => button.textContent)).toEqual([
      NOTHING_MATCHES.budgetFlexible,
      NOTHING_MATCHES.journeyFlexible("Cindermoor Works"),
    ]);
  });

  test("test_each_button_sends_the_one_edit_that_loosens_its_limit", async () => {
    const { user, sent } = show();

    for (const button of screen.getAllByRole("button")) await user.click(button);

    expect(sent).toEqual([edits.budgetStrictness("soft"), edits.placeStrictness("syn-p0021", "soft")]);
    for (const operations of sent) expect(problemsWith("Operations", operations)).toEqual([]);
  });

  test("test_a_limit_that_is_flexible_already_has_no_button", () => {
    const loose: PreferenceSpec = {
      ...nothing.spec,
      budget: { ...nothing.spec.budget, strictness: "soft" },
    };

    expect(waysOut(loose, areas, NAMES).map((way) => way.key)).toEqual(["place:syn-p0021"]);
    expect(waysOut({ ...loose, commutes: [] }, areas, NAMES)).toEqual([]);
  });

  test("test_a_hidden_area_and_an_only_rule_each_have_a_button_that_clears_them", () => {
    const ruled: PreferenceSpec = {
      ...nothing.spec,
      areas: [
        { area_id: "syn-n0003", rule: "exclude", provenance: "ui_edit" },
        { area_id: "syn-n0006", rule: "only", provenance: "stated" },
      ],
    };

    const ways = waysOut(ruled, areas, NAMES).slice(2);

    expect(ways.map((way) => way.label)).toEqual([
      NOTHING_MATCHES.showHidden("Cindermoor"),
      NOTHING_MATCHES.showAll("Farrowmere"),
    ]);
    expect(ways.map((way) => way.operations)).toEqual([edits.areaClear("syn-n0003"), edits.areaClear("syn-n0006")]);
  });

  test("test_where_no_limit_left_an_area_out_the_page_does_not_say_that_one_did", () => {
    // Seen in a browser: "No area passes every limit you set", of a person who had set
    // none. Every area had no figure for what counted, and nothing on the page named it.
    const lacking = areas.map((area) => ({
      area_id: area.area_id,
      reason: "insufficient_data" as const,
      missing: ["budget", "tag:leafy"],
    }));
    render(
      <NothingMatches
        filtered={[]}
        unranked={lacking}
        spec={{ ...nothing.spec, budget: { ...nothing.spec.budget, strictness: "soft" }, commutes: [] }}
        areas={areas}
        placeNames={NAMES}
        meta={meta}
        onEdit={() => undefined}
      />,
    );

    expect(screen.queryByRole("region", { name: NOTHING_MATCHES.title })).toBeNull();
    const block = within(screen.getByRole("region", { name: NOTHING_MATCHES.noData }));
    expect(document.body.textContent?.includes("limit")).toBe(false);
    // What has no figure is named, by the names the API gives, with how many areas lack it.
    const lacks = within(block.getByRole("list", { name: NOTHING_MATCHES.lacks }))
      .getAllByRole("listitem")
      .map((item) => item.textContent);
    expect(lacks).toEqual([`Budget: ${areas.length} areas`, `Leafy: ${areas.length} areas`]);
    expect(block.queryByRole("button")).toBeNull();
  });

  test("test_the_block_has_no_accessibility_fault", async () => {
    const { container } = show();

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("what is said when no area passes, as it is drawn", () => {
  test("test_it_stands_in_the_box_of_the_look_and_is_the_region_it_was", () => {
    show();
    const block = screen.getByRole("region", { name: NOTHING_MATCHES.title });

    expect(block.tagName).toBe("SECTION");
    expect(block).toHaveClass("frame", "box", "nothing");
    // The frame brings the cream it is read on. The block lays no ground of its own under it.
    expect(setsOf(".nothing").has("background")).toBe(false);
  });

  test("test_it_says_what_it_said_in_the_order_it_said_it", () => {
    show();
    const block = screen.getByRole("region", { name: NOTHING_MATCHES.title });

    expect([...block.children].map((part) => part.tagName)).toEqual(["H2", "P", "DL", "UL"]);
    expect(within(block).getByRole("heading", { level: 2 }).textContent).toBe(NOTHING_MATCHES.title);
    expect(block.querySelector("p")?.textContent).toBe(NOTHING_MATCHES.lead);
    expect(within(block).getByRole("list", { name: NOTHING_MATCHES.loosen })).toBe(block.lastElementChild);
  });

  test("test_its_heading_is_set_in_the_face_of_names_at_a_size_a_name_is_read_at", () => {
    expect(setsOf(".title").get("font")).toBe("400 var(--name-2) / 1.1 var(--font-name)");
    expect(setsOf(".title").get("font-synthesis")).toBe("none");
    // Every sentence and every figure of it is set in the reading face, which the page gives.
    const faces = STYLES.filter((rule) => rule.selector !== ".title" && [...rule.sets.keys()].some((property) => /^font(-family)?$/.test(property)));
    expect(faces.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_a_count_is_said_after_its_reason_and_is_drawn_before_it_on_a_chip_of_sand_in_ink", () => {
    show();
    const block = within(screen.getByRole("region", { name: NOTHING_MATCHES.title }));

    // A reason is a term and its count is what is said of it, as they were.
    for (const term of block.getAllByRole("term")) {
      expect(term.parentElement?.tagName).toBe("DIV");
      expect([...(term.parentElement?.children ?? [])].map((part) => part.tagName)).toEqual(["DT", "DD"]);
    }
    // The count is drawn first in its line, and the reason beside it.
    expect([setsOf(".counts dd").get("grid-column"), setsOf(".counts dt").get("grid-column")]).toEqual(["1", "2"]);
    expect([setsOf(".counts dd").get("grid-row"), setsOf(".counts dt").get("grid-row")]).toEqual(["1", "1"]);
    // Of the colours words are set in, ink alone is read on sand. The chip has an edge of ink.
    const chip = setsOf(".counts dd");
    expect([chip.get("background"), chip.get("color"), chip.get("border")]).toEqual([
      "var(--sand)",
      "var(--ink)",
      "var(--edge) solid var(--ink)",
    ]);
    expect(STYLES.filter((rule) => rule.sets.get("background") === "var(--sand)").map((rule) => rule.selector)).toEqual([
      ".counts dd",
    ]);
    // A reason is a sentence, and is read in ink at the size of one.
    expect([setsOf(".counts dt").get("color"), setsOf(".counts dt").get("font-size")]).toEqual(["var(--ink)", "var(--size-body)"]);
    // Figures stand under figures.
    expect(chip.get("font-variant-numeric")).toBe("tabular-nums");
  });

  test("test_each_way_out_is_a_button_of_the_look_in_cream_and_none_is_the_one_that_matters_most", () => {
    show();
    const ways = within(screen.getByRole("list", { name: NOTHING_MATCHES.loosen })).getAllByRole("button");

    expect(ways.length).toBeGreaterThan(1);
    for (const way of ways) {
      expect(way.tagName).toBe("BUTTON");
      expect(way).toHaveAttribute("type", "button");
      expect(way).toHaveClass("press", "target");
      // Search is the one cobalt button in sight, and two ways out are each as good as the other.
      expect(way.firstElementChild).toHaveAttribute("data-kind", "plain");
      expect(way).not.toHaveAttribute("aria-pressed");
    }
  });

  test("test_every_way_out_is_read_so_that_one_that_names_a_place_is_set_as_the_one_beside_it", () => {
    // Seen in a look: a way out that named an area with a figure in its name was set in the
    // reading face, as the kit sets every figure, and the way out beside it in the face of
    // names. A way out names what it loosens, and the name is the service's and may be long.
    const ruled: PreferenceSpec = {
      ...nothing.spec,
      areas: [{ area_id: areas[0]?.area_id ?? "", rule: "exclude", provenance: "ui_edit" }],
    };
    show(ruled);
    const ways = within(screen.getByRole("list", { name: NOTHING_MATCHES.loosen })).getAllByRole("button");

    expect(ways).toHaveLength(3);
    for (const way of ways) {
      expect([way.textContent, way.querySelector("[data-reads]")?.getAttribute("data-reads")]).toEqual([way.textContent, "true"]);
    }
  });

  test("test_the_keyboard_goes_from_one_way_out_to_the_next_and_a_key_sends_its_edit", async () => {
    const { user, sent } = show();
    const [first, second] = within(screen.getByRole("list", { name: NOTHING_MATCHES.loosen })).getAllByRole("button");

    await user.tab();
    expect(first).toHaveFocus();
    await user.keyboard("{Enter}");
    await user.tab();
    expect(second).toHaveFocus();
    await user.keyboard(" ");

    const [place = ""] = Object.keys(NAMES);
    expect(sent).toEqual([edits.budgetStrictness("soft"), edits.placeStrictness(place, "soft")]);
  });

  test("test_nothing_of_it_moves_and_nothing_of_it_is_keyed_on_the_pointer_or_the_focus", () => {
    expect(ALL.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition|transform)/.test(property)))).toEqual([]);
    expect(ALL.filter((rule) => /:(hover|focus|active)/.test(rule.selector))).toEqual([]);
  });

  test("test_nothing_that_holds_words_has_a_height_of_its_own", () => {
    expect(ALL.filter((rule) => rule.sets.has("height") || rule.sets.has("max-height")).map((rule) => rule.selector)).toEqual([]);
  });
});
