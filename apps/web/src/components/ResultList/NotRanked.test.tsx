import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { APART, UNRANKED } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Unranked } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { NotRanked } from "./NotRanked";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
/**
 * Leafy, quiet, a budget and a journey: one area has no figure for what was asked of the place,
 * which is most of what counts in the search.
 */
const first = recordedAnswer("rank", "rank-first").body.data;
const nameOf = (areaId: string) => areas.find((area) => area.area_id === areaId)?.name ?? "";
const apart = first.unranked.find((area) => area.reason === "insufficient_data") as Unranked;

const button = () => screen.getByRole("button", { name: APART.title(first.unranked.length) });
/** One item for each area. What an area lacks is a list of its own, inside its item. */
const items = () => [...screen.getByRole("list", { name: APART.label }).children] as HTMLElement[];
const itemOf = (areaId: string) => items().find((item) => item.getAttribute("data-area") === areaId) as HTMLElement;

describe("the areas that are not ranked", () => {
  test("test_an_area_burro_cannot_place_is_in_no_result_and_is_listed_apart", async () => {
    // It once came first, with a fit of 88, on its journey and its rent alone.
    const user = userEvent.setup({ delay: null });
    render(<NotRanked unranked={first.unranked} areas={areas} meta={meta} />);

    expect(nameOf(apart.area_id)).toBe("Otterby Fields");
    expect(first.scores.map((score) => score.area_id)).not.toContain(apart.area_id);
    expect(first.ranked.map((area) => area.area_id)).not.toContain(apart.area_id);
    await user.click(button());

    expect(items().map((item) => item.getAttribute("data-area")).sort()).toEqual(
      first.unranked.map((area) => area.area_id).sort(),
    );
    expect(itemOf(apart.area_id)).toHaveTextContent("Otterby Fields");
    expect(itemOf(apart.area_id)).toHaveTextContent(UNRANKED.insufficient_data);
  });

  test("test_an_area_with_a_journey_and_a_rent_and_no_character_says_that_it_is_the_character", async () => {
    // A rent and a workplace alone: the area has most of what counts, and none of the character.
    const user = userEvent.setup({ delay: null });
    const money = recordedAnswer("rank", "rank-money-and-work").body.data;
    const unknown = money.unranked.find((area) => area.reason === "character_unknown") as Unranked;
    render(<NotRanked unranked={money.unranked} areas={areas} meta={meta} />);
    await user.click(screen.getByRole("button", { name: APART.title(money.unranked.length) }));

    expect(nameOf(unknown.area_id)).toBe("Otterby Fields");
    expect(itemOf(unknown.area_id)).toHaveTextContent(UNRANKED.character_unknown);
  });

  test("test_an_area_this_search_cannot_place_comes_before_one_the_data_never_ranks", async () => {
    // Seen in a browser: the one area the search had left out stood between two that no search ranks.
    const user = userEvent.setup({ delay: null });
    render(<NotRanked unranked={first.unranked} areas={areas} meta={meta} />);
    await user.click(button());

    expect(first.unranked.map((area) => area.reason)).toEqual(["not_rankable", "insufficient_data", "not_rankable"]);
    expect(items().map((item) => item.getAttribute("data-area"))).toEqual([
      apart.area_id,
      ...first.unranked.filter((area) => area.reason === "not_rankable").map((area) => area.area_id),
    ]);
  });

  test("test_what_the_person_asked_for_is_said_before_the_settings_nobody_chose", async () => {
    // Seen in a browser: what Otterby Fields lacks began with four usual settings, and the
    // vibes that were asked for came last.
    const user = userEvent.setup({ delay: null });
    const spec = recordedAnswer("interpret", "interpret-first").body.data.spec;
    render(<NotRanked unranked={first.unranked} areas={areas} meta={meta} spec={spec} />);
    await user.click(button());
    const lacks = within(within(itemOf(apart.area_id)).getByRole("list", { name: APART.lacks }))
      .getAllByRole("listitem")
      .map((item) => item.textContent);

    expect(apart.missing.slice(-2)).toEqual(["tag:leafy", "tag:quiet_residential"]);
    expect(lacks.slice(0, 2)).toEqual(["Leafy", "Quiet streets"]);
    // Nothing is left out, and the rest are in the order the API gave them.
    expect(lacks).toHaveLength(apart.missing.length);
    const usual = apart.missing.slice(0, -2).map((component) => meta.features.find((one) => `feature:${one.feature_id}` === component)?.label);
    expect(lacks.slice(2)).toEqual(usual);
  });

  test("test_it_is_closed_at_first_and_says_how_many_areas_it_holds", () => {
    render(<NotRanked unranked={first.unranked} areas={areas} meta={meta} />);

    expect(first.unranked).toHaveLength(3);
    expect(button()).toHaveAttribute("aria-expanded", "false");
    expect(button()).toHaveTextContent("3 areas are not ranked");
    expect(screen.queryByRole("list", { name: APART.label })).toBeNull();
    expect(screen.queryByText("Otterby Fields")).toBeNull();
    expect(APART.title(1)).toBe("1 area is not ranked");
  });

  test("test_each_area_says_what_it_has_no_figure_for_by_the_names_the_api_gives", async () => {
    const user = userEvent.setup({ delay: null });
    render(<NotRanked unranked={first.unranked} areas={areas} meta={meta} />);
    await user.click(button());

    const lacks = within(itemOf(apart.area_id)).getByRole("list", { name: APART.lacks });
    const named = within(lacks).getAllByRole("listitem").map((item) => item.textContent);

    expect(apart.missing).toContain("tag:leafy");
    expect(apart.missing).toContain("tag:quiet_residential");
    expect(named).toHaveLength(apart.missing.length);
    expect(named).toContain("Leafy");
    expect(named).toContain("Quiet streets");
    // A feature is named by the label the API gives it, and never by its id.
    expect(named).toContain(meta.features.find((feature) => feature.feature_id === "air_no2")?.label);
    expect(named.some((name) => /[:_]/.test(name ?? ""))).toBe(false);
  });

  test("test_an_area_the_data_does_not_rank_at_all_says_so_and_lists_nothing_it_lacks", async () => {
    const user = userEvent.setup({ delay: null });
    render(<NotRanked unranked={first.unranked} areas={areas} meta={meta} />);
    await user.click(button());
    const never = first.unranked.find((area) => area.reason === "not_rankable") as Unranked;

    expect(never.missing).toEqual([]);
    expect(itemOf(never.area_id)).toHaveTextContent(UNRANKED.not_rankable);
    expect(within(itemOf(never.area_id)).queryByRole("list")).toBeNull();
    expect(itemOf(never.area_id).textContent?.includes(APART.lacks)).toBe(false);
  });

  test("test_the_name_of_each_leads_to_the_page_of_the_area_and_is_not_fetched_ahead", async () => {
    const user = userEvent.setup({ delay: null });
    render(<NotRanked unranked={first.unranked} areas={areas} meta={meta} />);
    await user.click(button());

    for (const area of first.unranked) {
      const slug = areas.find((one) => one.area_id === area.area_id)?.slug;
      const link = within(itemOf(area.area_id)).getByRole("link", { name: nameOf(area.area_id) });
      expect(link).toHaveAttribute("href", `/synthetic/${slug}`);
      expect(link).toHaveAttribute("data-prefetch", "false");
    }
  });

  test("test_no_fit_no_rank_and_no_figure_is_given_for_an_area_that_is_not_ranked", async () => {
    const user = userEvent.setup({ delay: null });
    const { container } = render(<NotRanked unranked={first.unranked} areas={areas} meta={meta} />);
    await user.click(button());

    // The only figures are in the names the API gives its features, and in the count of the areas.
    const labels = meta.features.map((feature) => feature.label).join(" ");
    const figures = (container.textContent ?? "").match(/\d+/g) ?? [];
    expect(figures.filter((figure) => !labels.includes(figure) && figure !== "3")).toEqual([]);
    expect(/fit|rank \d/i.test(itemOf(apart.area_id).textContent ?? "")).toBe(false);
  });

  test("test_an_area_the_page_has_no_name_for_and_a_thing_it_has_no_name_for_are_left_out", async () => {
    const user = userEvent.setup({ delay: null });
    const newer: Unranked[] = [
      { area_id: "syn-n9999", reason: "character_unknown", missing: ["tag:leafy"] },
      { ...apart, missing: ["tag:leafy", "feature:not_known_here", "tag:not_known_here"] },
    ];
    const { container } = render(<NotRanked unranked={newer} areas={areas} meta={meta} />);
    await user.click(screen.getByRole("button", { name: APART.title(1) }));

    expect(items()).toHaveLength(1);
    expect(within(itemOf(apart.area_id)).getByRole("list", { name: APART.lacks }).textContent).toBe("Leafy");
    expect(container.textContent?.includes("not_known_here")).toBe(false);
    expect(container.textContent?.includes("syn-n9999")).toBe(false);
  });

  test("test_a_reason_the_page_has_no_words_for_is_left_out_and_never_shown_as_its_code_or_a_blank", async () => {
    const user = userEvent.setup({ delay: null });
    const newer = [{ ...apart, reason: "under_review" }] as unknown as Unranked[];
    const { container } = render(<NotRanked unranked={newer} areas={areas} meta={meta} />);
    await user.click(screen.getByRole("button", { name: APART.title(1) }));

    expect(itemOf(apart.area_id)).toHaveTextContent("Otterby Fields");
    expect(container.textContent?.includes("under_review")).toBe(false);
    expect([...container.querySelectorAll("p")].filter((line) => line.textContent === "")).toEqual([]);
  });

  test("test_an_answer_that_does_not_say_what_an_area_lacks_is_drawn_without_it", async () => {
    // An older service says why an area is not ranked, and not what it has no figure for.
    const user = userEvent.setup({ delay: null });
    const older = [{ area_id: apart.area_id, reason: "insufficient_data" }] as unknown as Unranked[];
    render(<NotRanked unranked={older} areas={areas} meta={meta} />);
    await user.click(screen.getByRole("button", { name: APART.title(1) }));

    expect(itemOf(apart.area_id)).toHaveTextContent(UNRANKED.insufficient_data);
    expect(within(itemOf(apart.area_id)).queryByRole("list")).toBeNull();
  });

  test("test_with_every_area_ranked_nothing_is_drawn", () => {
    const { container } = render(<NotRanked unranked={[]} areas={areas} meta={meta} />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_the_list_has_no_accessibility_fault", async () => {
    const user = userEvent.setup({ delay: null });
    const { container } = render(<NotRanked unranked={first.unranked} areas={areas} meta={meta} />);
    await user.click(button());

    expect(await faultsIn(container)).toEqual([]);
  });
});
