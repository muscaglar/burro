import { act, render, renderHook, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import { recordedAnswer } from "@/lib/api/recorded";
import { SearchProvider, useOpenSearch, useSearch } from "@/lib/search/store";

import { standInApi } from "../../../test/support/api";
import { watch } from "../../../test/support/watch";
import { createSession, SessionBoundary, SessionProvider, useCompare, useMadeLink } from "./session";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const ranked = recordedAnswer("rank", "rank-first").body.data;

const inASession = ({ children }: { children: ReactNode }) => <SessionProvider>{children}</SessionProvider>;

describe("the areas chosen to compare, in a session", () => {
  test("test_an_area_chosen_in_one_part_of_the_page_is_chosen_in_every_part", () => {
    const Button = () => {
      const { toggle } = useCompare();
      return (
        <button type="button" onClick={() => areas[0] && toggle(areas[0])}>
          choose
        </button>
      );
    };
    const Count = () => <p>{useCompare().chosen.map((area) => area.name).join(", ") || "none"}</p>;
    render(
      <SessionProvider>
        <Button />
        <Count />
      </SessionProvider>,
    );

    expect(screen.getByText("none")).toBeInTheDocument();
    act(() => screen.getByRole("button").click());

    expect(screen.getByText(areas[0]?.name ?? "")).toBeInTheDocument();
  });

  test("test_a_fifth_area_is_not_added", () => {
    const { result } = renderHook(() => useCompare(), { wrapper: inASession });

    act(() => areas.slice(0, 6).forEach((area) => result.current.toggle(area)));

    expect(result.current.chosen).toHaveLength(4);
    expect(result.current.full).toBe(true);
  });

  test("test_opening_a_comparison_puts_its_areas_in_place_of_what_was_chosen", () => {
    const { result } = renderHook(() => useCompare(), { wrapper: inASession });
    act(() => areas.slice(0, 3).forEach((area) => result.current.toggle(area)));

    act(() => result.current.set(areas.slice(5, 7)));

    expect(result.current.chosen.map((area) => area.slug)).toEqual(areas.slice(5, 7).map((area) => area.slug));
    expect(result.current.enough).toBe(true);
  });

  test("test_outside_a_session_nothing_is_chosen_and_nothing_breaks", () => {
    const { result } = renderHook(() => useCompare());

    act(() => areas[0] && result.current.toggle(areas[0]));

    expect(result.current.chosen).toEqual([]);
  });

  test("test_a_part_shown_on_its_own_holds_a_session_of_its_own", () => {
    const { result } = renderHook(() => useCompare(), {
      wrapper: ({ children }: { children: ReactNode }) => <SessionBoundary>{children}</SessionBoundary>,
    });

    act(() => areas[0] && result.current.toggle(areas[0]));

    expect(result.current.chosen).toHaveLength(1);
  });

  test("test_what_is_chosen_is_kept_in_memory_and_nowhere_else", () => {
    const watching = watch();
    try {
      const { result } = renderHook(() => useCompare(), { wrapper: inASession });
      act(() => areas.slice(0, 3).forEach((area) => result.current.toggle(area)));
      act(() => result.current.clear());

      expect(watching.storage).toEqual([]);
      expect(watching.history).toEqual([]);
      expect(watching.console).toEqual([]);
    } finally {
      watching.stop();
    }
  });
});

describe("the link a session holds", () => {
  const made = { of: "hash-one", exact: false, share: recordedAnswer("create_share", "share-made").body.data };

  test("test_a_link_that_was_made_is_there_for_every_part_of_the_page_and_when_it_is_come_back_to", () => {
    const first = renderHook(() => useMadeLink(), { wrapper: inASession });
    expect(first.result.current[0]).toBeNull();

    act(() => first.result.current[1](made));

    expect(first.result.current[0]).toBe(made);
  });

  test("test_a_link_is_kept_by_the_session_and_not_by_the_part_that_made_it", () => {
    const session = createSession();

    session.link.set(made);

    expect(session.link.get()).toBe(made);
    expect(createSession().link.get()).toBeNull();
  });

  test("test_outside_a_session_no_link_is_kept_and_nothing_breaks", () => {
    const { result } = renderHook(() => useMadeLink());

    act(() => result.current[1](made));

    expect(result.current[0]).toBeNull();
  });

  test("test_a_link_is_kept_in_memory_and_nowhere_else", () => {
    const watching = watch();
    try {
      const { result } = renderHook(() => useMadeLink(), { wrapper: inASession });
      act(() => result.current[1](made));

      expect(watching.storage).toEqual([]);
      expect(watching.history).toEqual([]);
      expect(watching.console).toEqual([]);
    } finally {
      watching.stop();
    }
  });
});

describe("the search a session holds", () => {
  function Spec() {
    const { state } = useSearch();
    return <p data-testid="hash">{state.specHash ?? "none"}</p>;
  }
  function Elsewhere() {
    const open = useOpenSearch();
    return <p data-testid="elsewhere">{open === null ? "no search" : (open.specHash ?? "a default")}</p>;
  }
  function Ranker() {
    const { flow } = useSearch();
    return (
      <button type="button" onClick={() => void flow.rankNow()}>
        rank
      </button>
    );
  }

  test("test_a_search_is_still_there_when_the_person_comes_back_to_the_page", async () => {
    const api = standInApi().on("rank", "rank-first").on("explain_top", "explanations-first");
    const page = (children: ReactNode) => <SessionProvider>{children}</SessionProvider>;
    const search = (
      <SearchProvider meta={meta} areas={areas} client={api.client}>
        <Spec />
        <Ranker />
      </SearchProvider>
    );
    const { rerender } = render(page(search));
    await act(async () => {
      screen.getByRole("button", { name: "rank" }).click();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(screen.getByTestId("hash")).toHaveTextContent(ranked.spec_hash);

    // The person follows a link to another page, and then comes back.
    rerender(page(<Elsewhere />));
    expect(screen.getByTestId("elsewhere")).toHaveTextContent(ranked.spec_hash);
    rerender(page(search));

    expect(screen.getByTestId("hash")).toHaveTextContent(ranked.spec_hash);
    expect(api.callsTo("rank")).toHaveLength(1);
  });

  test("test_a_page_loaded_afresh_holds_no_search", () => {
    render(
      <SessionProvider>
        <Elsewhere />
      </SessionProvider>,
    );

    expect(screen.getByTestId("elsewhere")).toHaveTextContent("no search");
    expect(createSession().search()).toBeNull();
  });

  test("test_a_search_shown_outside_a_session_is_its_own", () => {
    const api = standInApi();
    const one = render(
      <SearchProvider meta={meta} areas={areas} client={api.client}>
        <Spec />
      </SearchProvider>,
    );
    one.unmount();

    render(
      <SearchProvider meta={meta} areas={areas} client={api.client}>
        <Spec />
      </SearchProvider>,
    );

    expect(screen.getByTestId("hash")).toHaveTextContent("none");
  });
});
