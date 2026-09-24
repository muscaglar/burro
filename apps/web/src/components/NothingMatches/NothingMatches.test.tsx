import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FILTERED, NOTHING_MATCHES, UNRANKED } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { faultsIn } from "../../../test/support/axe";
import { problemsWith } from "../../../test/support/contract";
import { NothingMatches, waysOut } from "./NothingMatches";

const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const nothing = recordedAnswer("rank", "rank-nothing-matches").body.data;
const meta = recordedAnswer("get_meta", "meta").body.data;
const NAMES = { "syn-p0021": "Cindermoor Works" };

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
