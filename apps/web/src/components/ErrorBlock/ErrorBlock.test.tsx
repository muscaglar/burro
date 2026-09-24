import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FAILURE, NOTICE, PROMPT } from "@/content/search";
import type { ClientFailureKind, Failure } from "@/lib/api/failure";
import { recordedAnswer, recordedError } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";
import { edits, NO_EDITS } from "@/lib/search/edits";
import { isStale, repairsFor } from "@/lib/search/repairs";

import { faultsIn } from "../../../test/support/axe";
import { CANARY } from "../../../test/support/search";
import { ErrorBlock, wordsFor } from "./ErrorBlock";

function fromThe(scenario: string): Failure {
  const recorded = recordedError(scenario);
  return {
    kind: "api",
    status: recorded.status,
    code: recorded.body.error.code,
    message: recorded.body.error.message,
    fields: recorded.body.error.fields,
    meta: recorded.body.meta,
    synthetic: true,
    requestId: recorded.headers["x-request-id"] ?? null,
  };
}

const notTheApis = (kind: ClientFailureKind): Failure => ({ kind, status: null, synthetic: null, requestId: null });
const stale = (recordedAnswer("rank", "rank-stale-spec-repaired").request.body as { spec: PreferenceSpec }).spec;

function show(failure: Failure, props: Partial<Parameters<typeof ErrorBlock>[0]> = {}) {
  const told = { onRetry: jest.fn(), onStartAgain: jest.fn(), onEdit: jest.fn<void, [Operations]>() };
  const view = render(<ErrorBlock failure={failure} notUpdated={false} {...told} {...props} />);
  return { ...told, user: userEvent.setup({ delay: null }), ...view };
}

describe("what is said of a failure", () => {
  test("test_the_apis_own_words_are_shown_as_they_came_with_the_id_to_quote", () => {
    const fault = fromThe("error-internal");
    show(fault, { notUpdated: true });

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(recordedError("error-internal").body.error.message);
    expect(alert).toHaveTextContent(NOTICE.notUpdated);
    expect(alert).toHaveTextContent(`${NOTICE.requestId} ${fault.requestId}`);
  });

  test.each(["timeout", "network", "unreadable", "not_configured"] as const)(
    "test_a_failure_that_is_not_the_apis_has_words_of_its_own: %s",
    (kind) => {
      show(notTheApis(kind));

      expect(screen.getByRole("alert")).toHaveTextContent(FAILURE[kind]);
      expect(screen.queryByText(NOTICE.requestId, { exact: false })).toBeNull();
      expect(FAILURE[kind].length).toBeGreaterThan(10);
    },
  );

  test("test_nothing_that_was_sent_is_shown_because_nothing_that_was_sent_is_given", () => {
    // A failure holds codes, paths and fixed words. There is nowhere in it for what was typed.
    const refusal = fromThe("rank-invalid-operations");

    expect(JSON.stringify(refusal).includes(CANARY)).toBe(false);
    expect(Object.keys(refusal).sort()).toEqual(
      ["code", "fields", "kind", "message", "meta", "requestId", "status", "synthetic"].sort(),
    );
    expect(wordsFor(refusal)).toBe("The operations are not valid.");
  });

  test("test_trying_again_and_starting_again_are_buttons_of_full_size", async () => {
    const { user, onRetry, onStartAgain } = show(fromThe("error-internal"));

    await user.click(screen.getByRole("button", { name: PROMPT.tryAgain }));
    await user.click(screen.getByRole("button", { name: PROMPT.startAgain }));

    expect(onRetry).toHaveBeenCalledTimes(1);
    expect(onStartAgain).toHaveBeenCalledTimes(1);
    for (const button of screen.getAllByRole("button")) expect(button).toHaveClass("target");
  });

  test("test_the_block_has_no_accessibility_fault", async () => {
    const { container } = show(fromThe("error-internal"), { notUpdated: true });

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("a search that names something the data no longer has", () => {
  const failure = fromThe("rank-stale-spec");

  test("test_the_page_says_so_in_its_own_words_and_offers_to_take_it_out", async () => {
    const repairs = repairsFor(failure, stale, NO_EDITS);
    const { user, onEdit } = show(failure, { repairs, nameOf: () => null });

    expect(isStale(failure)).toBe(true);
    expect(screen.getByRole("alert")).toHaveTextContent(NOTICE.stale);
    await user.click(screen.getByRole("button", { name: NOTICE.takeOut(NOTICE.thePlace) }));

    // The edit is the one the API was recorded accepting the same spec with.
    const repaired = recordedAnswer("rank", "rank-stale-spec-repaired").request.body as {
      operations: Operations;
    };
    expect(onEdit).toHaveBeenCalledWith(repaired.operations);
  });

  test("test_the_path_is_read_as_a_position_in_the_spec_the_api_last_returned", () => {
    expect(failure.kind === "api" && failure.fields).toEqual([
      { path: "spec.commutes[1].place_id", problem: "unknown_place" },
    ]);
    expect(stale.commutes.map((commute) => commute.place_id)).toEqual(["syn-p0021", "syn-p9999"]);

    expect(repairsFor(failure, stale, NO_EDITS)).toEqual([
      { what: "place", key: "place:syn-p9999", operations: edits.placeRemove("syn-p9999") },
    ]);
  });

  test("test_each_kind_of_thing_that_can_be_gone_has_the_edit_that_takes_it_out", () => {
    const spec = {
      ...stale,
      areas: [{ area_id: "syn-n9999", rule: "exclude", provenance: "stated" }],
    } as const;
    const gone = (path: string): Failure => ({ ...failure, fields: [{ path, problem: "not_in_release" }] }) as Failure;

    expect(repairsFor(gone("spec.areas[0].area_id"), spec, NO_EDITS)[0]?.operations).toEqual(
      edits.areaClear("syn-n9999"),
    );
    expect(repairsFor(gone("spec.weights[0].feature_id"), spec, NO_EDITS)[0]?.operations).toEqual(
      edits.featureOff(spec.weights[0]?.feature_id ?? "air_no2"),
    );
    expect(repairsFor(gone("spec.tags[1]"), spec, NO_EDITS)[0]?.operations).toEqual(
      edits.tagOff(spec.tags[1]?.tag_id ?? "leafy"),
    );
  });

  test("test_no_repair_is_offered_for_what_cannot_be_taken_out_or_is_not_there", () => {
    const at = (path: string): Failure => ({ ...failure, fields: [{ path, problem: "out_of_range" }] }) as Failure;

    expect(repairsFor(at("spec.budget.amount"), stale, NO_EDITS)).toEqual([]);
    expect(repairsFor(at("spec.commutes[7].place_id"), stale, NO_EDITS)).toEqual([]);
    expect(repairsFor(at("operations.tag_ops[0].tag_id"), stale, NO_EDITS)).toEqual([]);
    expect(repairsFor(fromThe("error-internal"), stale, NO_EDITS)).toEqual([]);
    expect(repairsFor(notTheApis("timeout"), stale, NO_EDITS)).toEqual([]);
    expect(repairsFor(null, stale, NO_EDITS)).toEqual([]);
  });

  test("test_no_repair_is_offered_while_edits_are_waiting_because_the_positions_are_not_known", () => {
    // A path counts positions in the spec as the waiting edits leave it, which the website does not hold.
    expect(repairsFor(failure, stale, edits.placeAdd("syn-p0001"))).toEqual([]);
  });

  test("test_the_same_thing_is_offered_once_however_many_paths_name_it", () => {
    const twice = {
      ...failure,
      fields: [
        { path: "spec.commutes[1].place_id", problem: "unknown_place" },
        { path: "spec.commutes[1].max_minutes", problem: "out_of_range" },
      ],
    } as Failure;

    expect(repairsFor(twice, stale, NO_EDITS)).toHaveLength(1);
  });
});
