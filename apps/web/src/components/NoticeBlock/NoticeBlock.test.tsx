import { render, screen } from "@testing-library/react";

import { NOTICE, REJECTED, REJECTED_LABEL, STATUS, UNMET, UNMET_LABEL } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { RejectReason, UnmetCategory } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { statusOf, StatusLine } from "../StatusLine/StatusLine";
import { NoticeBlock, OfflineLine, RejectedList, StateLine, UnmetList } from "./NoticeBlock";

const notice = recordedAnswer("interpret", "interpret-notice").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("rank", "rank-first").body.data;

describe("the neutral notice", () => {
  test("test_the_apis_sentence_is_shown_word_for_word_as_a_status", () => {
    render(<NoticeBlock notice={notice.notice} text={notice.notice_text} />);

    const block = screen.getByRole("status", { name: NOTICE.label });
    expect(block.textContent).toBe(notice.notice_text);
    expect(notice.notice_text).toBe(
      "Burro ranks places by what is there. Of who lives in a place it counts only their age and their households, at the census of 2021, and you cannot ask for fewer of anyone. The rest of your search has been applied.",
    );
  });

  test("test_with_no_notice_there_is_no_block", () => {
    const { container } = render(<NoticeBlock notice="none" text="" />);

    expect(container).toBeEmptyDOMElement();
  });

  test("test_the_website_has_no_words_of_its_own_for_the_notice", () => {
    // Whatever the API says is what is shown, so the words are the same for every group and every person.
    render(<NoticeBlock notice="neutral_places" text="Whatever the API says." />);

    expect(screen.getByRole("status")).toHaveTextContent(/^Whatever the API says\.$/);
  });
});

describe("what could not be answered, and what was not applied", () => {
  test("test_every_kind_of_unmet_request_has_a_line_of_its_own", () => {
    const every = Object.keys(UNMET) as UnmetCategory[];
    render(<UnmetList unmet={every} />);

    expect(screen.getByRole("region", { name: UNMET_LABEL })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem").map((line) => line.textContent)).toEqual(every.map((one) => UNMET[one]));
    expect(new Set(Object.values(UNMET)).size).toBe(15);
  });

  test("test_every_reason_an_edit_can_be_refused_for_has_words", () => {
    const every = Object.keys(REJECTED) as RejectReason[];
    render(
      <RejectedList
        refusals={every.map((reason) => ({ key: null, reason }))}
        nameOf={() => null}
      />,
    );

    expect(screen.getByRole("region", { name: REJECTED_LABEL })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(11);
    expect(new Set(Object.values(REJECTED)).size).toBe(11);
  });

  test("test_a_refusal_names_what_it_was_about_where_that_has_a_name", () => {
    render(
      <RejectedList
        refusals={[
          { key: "feature:crime_burglary_theft", reason: "crime_needs_explicit_request" },
          { key: "budget", reason: "out_of_range" },
        ]}
        nameOf={(key) => (key.startsWith("feature:") ? "Recorded burglary and theft" : null)}
      />,
    );

    expect(screen.getAllByRole("listitem").map((line) => line.textContent)).toEqual([
      `Recorded burglary and theft: ${REJECTED.crime_needs_explicit_request}`,
      REJECTED.out_of_range,
    ]);
  });

  test("test_with_nothing_to_say_there_is_nothing_on_the_page", () => {
    const { container } = render(
      <>
        <UnmetList unmet={[]} />
        <RejectedList refusals={[]} nameOf={() => null} />
      </>,
    );

    expect(container).toBeEmptyDOMElement();
  });

  test("test_no_word_for_a_refusal_calls_a_place_safe_or_unsafe", () => {
    const words = [...Object.values(REJECTED), ...Object.values(UNMET)].join(" ");

    expect(/\b(safe|unsafe|dangerous|rough|dodgy|sketchy)\b/i.test(words)).toBe(false);
  });
});

describe("the lines that say a state", () => {
  test("test_offline_is_said_as_a_status_and_says_when_an_edit_is_waiting", () => {
    const { rerender } = render(<OfflineLine waiting={false} />);
    expect(screen.getByRole("status")).toHaveTextContent(new RegExp(`^${NOTICE.offline}$`));

    rerender(<OfflineLine waiting />);
    expect(screen.getByRole("status")).toHaveTextContent(`${NOTICE.offline} ${NOTICE.offlineWaiting}`);
  });

  test("test_each_state_has_one_thing_to_say", () => {
    const shared = { areas, moved: null, gaveWay: false };
    const ranking = { ...first };

    expect(statusOf({ ...shared, phase: "empty", ranking: null })).toBe("");
    expect(statusOf({ ...shared, phase: "interpreting", ranking: null })).toBe(STATUS.reading);
    expect(statusOf({ ...shared, phase: "interpreting", ranking })).toBe(STATUS.reading);
    expect(statusOf({ ...shared, phase: "results", ranking })).toBe("21 areas ranked. First: Farrowmere.");
    expect(statusOf({ ...shared, phase: "results", ranking, gaveWay: true })).toBe(
      `21 areas ranked. First: Farrowmere. ${STATUS.gaveWay}`,
    );
    // What was asked of the place leads, until a person makes a journey or a budget count for more.
    const asked = recordedAnswer("interpret", "interpret-first").body.data.spec;
    expect(statusOf({ ...shared, phase: "results", ranking, gaveWay: true, spec: asked })).toBe(
      `21 areas ranked. First: Farrowmere. ${STATUS.gaveWay}`,
    );
    // Where a journey and a budget outweigh what was asked of the place, the line says so,
    // whether or not anything gave way: it is what explains the order on screen.
    const spec = { ...asked, commute_weight: 1, budget: { ...asked.budget, weight: 0.8 } };
    for (const gaveWay of [true, false]) {
      expect(statusOf({ ...shared, phase: "results", ranking, gaveWay, spec })).toBe(
        `21 areas ranked. First: Farrowmere. ${STATUS.leads(1, true)}`,
      );
    }
    expect(statusOf({ ...shared, phase: "results", ranking, moved: 3, spec })).toBe(
      `3 areas changed place. ${STATUS.leads(1, true)}`,
    );
    // With nothing asked of the place, what was asked for is the journey and the budget.
    const money = recordedAnswer("interpret", "interpret-money-and-work").body.data.spec;
    expect(statusOf({ ...shared, phase: "results", ranking, gaveWay: true, spec: money })).toBe(
      `21 areas ranked. First: Farrowmere. ${STATUS.gaveWay}`,
    );
    expect([STATUS.leads(1, true), STATUS.leads(2, true), STATUS.leads(1, false), STATUS.leads(2, false), STATUS.leads(0, true)]).toEqual([
      "Journey and budget count most.",
      "Journeys and budget count most.",
      "Journey counts most.",
      "Journeys count most.",
      "Budget counts most.",
    ]);
    expect(statusOf({ ...shared, phase: "results", ranking, moved: 3 })).toBe("3 areas changed place.");
    expect(statusOf({ ...shared, phase: "results", ranking, moved: 1 })).toBe("1 area changed place.");
    expect(statusOf({ ...shared, phase: "results", ranking, moved: 0 })).toBe("No area changed place.");
    // Where no area is ranked, a limit is blamed only where a limit left an area out.
    const left = [{ area_id: "syn-n0001", reason: "over_budget" as const }];
    expect(statusOf({ ...shared, phase: "results", ranking: { ...ranking, ranked: [], filtered: left } })).toBe(
      STATUS.nothingMatches,
    );
    expect(statusOf({ ...shared, phase: "results", ranking: { ...ranking, ranked: [], filtered: [] } })).toBe(
      STATUS.nothingRanked,
    );
    expect(statusOf({ ...shared, phase: "empty", ranking: null, asking: true })).toBe(STATUS.question);
  });

  test("test_a_ranking_that_follows_one_of_no_area_is_said_as_a_first_ranking_is", () => {
    // Seen in a browser: "1002 areas ranked, 1002 more than before. The rest are in the
    // order they were." There was no rest: no area had been ranked before.
    const shared = { areas, gaveWay: false, phase: "results" as const, ranking: first };
    const now = first.scores.length;

    expect(statusOf({ ...shared, moved: 0, was: 0 })).toBe(`${now} areas ranked. First: Farrowmere.`);
  });

  test("test_when_fewer_or_more_areas_are_ranked_the_line_says_so_and_counts_only_those_that_moved", () => {
    // Seen in a browser: "21 areas changed place" when the list went from 20 to 15.
    const shared = { areas, gaveWay: false, phase: "results" as const, ranking: first };
    const now = first.scores.length;

    expect(statusOf({ ...shared, moved: 0, was: now + 6 })).toBe(
      `${now} areas ranked, 6 fewer than before. The rest are in the order they were.`,
    );
    expect(statusOf({ ...shared, moved: 2, was: now - 1 })).toBe(
      `${now} areas ranked, 1 more than before. 2 of the rest changed place.`,
    );
    expect(statusOf({ ...shared, moved: 1, was: now + 1 })).toBe(
      `${now} areas ranked, 1 fewer than before. 1 of the rest changed place.`,
    );
    // The same number as before: only what moved is said.
    expect(statusOf({ ...shared, moved: 3, was: now })).toBe("3 areas changed place.");
  });

  test("test_an_area_the_page_has_no_name_for_is_never_named_as_nothing", () => {
    const shared = { areas, moved: null, gaveWay: false, phase: "results" as const };
    const [top, ...rest] = first.ranked;
    const unknown = { ...first, ranked: [{ ...(top as (typeof first.ranked)[number]), area_id: "syn-n9999" }, ...rest] };
    const second = areas.find((area) => area.area_id === rest[0]?.area_id)?.name ?? "no name";

    // The first result the page can name is named, and never "First: ." with nothing after it.
    expect(statusOf({ ...shared, ranking: unknown })).toBe(`21 areas ranked. First: ${second}.`);
    expect(
      statusOf({ ...shared, ranking: { ...first, ranked: first.ranked.map((area) => ({ ...area, area_id: "syn-n9999" })) } }),
    ).toBe("21 areas ranked.");
  });

  test("test_while_an_edit_is_ranked_the_line_keeps_what_it_said", () => {
    const shared = { areas, ranking: first, moved: 4, gaveWay: false };

    expect(statusOf({ ...shared, phase: "refining" })).toBe(statusOf({ ...shared, phase: "results" }));
  });

  test("test_with_nothing_to_rank_by_the_line_says_the_areas_are_in_no_order", () => {
    const empty = recordedAnswer("rank", "rank-empty-spec").body.data;

    expect(statusOf({ areas, phase: "results", ranking: empty, moved: null, gaveWay: false })).toBe(
      STATUS.rankedNoOrder(22),
    );
  });

  test("test_the_status_line_is_a_polite_live_region_that_is_always_on_the_page", () => {
    const { rerender } = render(
      <StatusLine phase="empty" ranking={null} areas={areas} moved={null} gaveWay={false} />,
    );
    const line = screen.getByRole("status");
    expect(line).toHaveAttribute("aria-live", "polite");
    expect(line).toBeEmptyDOMElement();

    rerender(<StatusLine phase="interpreting" ranking={null} areas={areas} moved={null} gaveWay={false} />);
    // The same element says the next thing, so a screen reader hears the change.
    expect(screen.getByRole("status")).toBe(line);
    expect(line).toHaveTextContent(STATUS.reading);
  });

  test("test_the_lines_have_no_accessibility_fault", async () => {
    const { container } = render(
      <>
        <NoticeBlock notice={notice.notice} text={notice.notice_text} />
        <StateLine>{NOTICE.degraded}</StateLine>
        <UnmetList unmet={["broadband", "other"]} />
        <RejectedList refusals={[{ key: "budget", reason: "out_of_range" }]} nameOf={() => "Budget"} />
        <OfflineLine waiting />
      </>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
