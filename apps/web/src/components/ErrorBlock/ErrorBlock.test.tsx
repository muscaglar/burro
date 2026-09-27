import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FAILURE, NOTICE, PROMPT } from "@/content/search";
import type { ClientFailureKind, Failure } from "@/lib/api/failure";
import { recordedAnswer, recordedError } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";
import { edits, NO_EDITS } from "@/lib/search/edits";
import { isStale, repairsFor } from "@/lib/search/repairs";

import { faultsIn } from "../../../test/support/axe";
import { asWritten } from "../../../test/support/contrast";
import { rulesOf } from "../../../test/support/css";
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

  test("test_an_answer_that_is_not_burros_own_says_by_its_status_that_burro_is_busy_or_has_a_fault", () => {
    // Seen in a browser, of an answer of 429 whose body was a page and no answer of Burro's:
    // "Burro sent back an answer that this page could not understand.", with "Try again"
    // beside it. Nothing said to wait, and trying again at once is what such an answer refuses.
    const answered = (status: number | null): Failure => ({ kind: "unreadable", status, synthetic: null, requestId: null });

    expect(wordsFor(answered(429))).toBe(FAILURE.busy);
    for (const status of [500, 502, 503, 504]) expect([status, wordsFor(answered(status))]).toEqual([status, FAILURE.fault]);
    // An answer that says all went well, and cannot be read, is what it was said to be.
    for (const status of [200, 404, null]) expect([status, wordsFor(answered(status))]).toEqual([status, FAILURE.unreadable]);
    // Only the one that was refused for asking too often says to wait.
    expect(FAILURE.busy).toMatch(/\bwait\b/);
    expect(new Set([FAILURE.busy, FAILURE.fault, FAILURE.unreadable]).size).toBe(3);
    // What is Burro's own is said in Burro's words, whatever its status.
    expect(wordsFor(fromThe("error-internal"))).toBe(recordedError("error-internal").body.error.message);

    show(answered(429));
    expect(screen.getByRole("alert")).toHaveTextContent(FAILURE.busy);
  });

  test("test_nothing_that_was_sent_is_shown_because_nothing_that_was_sent_is_given", () => {
    // A failure holds codes, paths and fixed words. There is nowhere in it for what was typed.
    const refusal = fromThe("rank-invalid-operations");

    expect(JSON.stringify(refusal).includes(CANARY)).toBe(false);
    expect(Object.keys(refusal).sort()).toEqual(
      ["code", "fields", "kind", "message", "meta", "requestId", "status", "synthetic"].sort(),
    );
    // What is shown is the service's sentence for the failure, word for word as it came. The
    // service wrote its sentences again for a person who has never seen Burro, and each is
    // fixed text as it was: one sentence for a code, whatever was sent.
    expect(wordsFor(refusal)).toBe(recordedError("rank-invalid-operations").body.error.message);
    expect(wordsFor(refusal)).toBe("Burro could not make that change to your search.");
    // It says where in what was sent the fault stands, and never what stood there.
    expect(refusal.kind === "api" && refusal.fields.map((field) => Object.keys(field).sort())).toEqual(
      recordedError("rank-invalid-operations").body.error.fields.map(() => ["path", "problem"]),
    );
  });

  test("test_the_id_of_a_place_that_was_sent_is_in_no_failure_and_in_nothing_the_block_shows", () => {
    // The id of a place says where someone needs to be. A search that names a place the data
    // no longer has was sent with that id, and is refused by where the place stood in it.
    const recorded = recordedError("rank-stale-spec");
    const sent = (recorded.request.body as { spec: PreferenceSpec }).spec.commutes.map((commute) => commute.place_id);
    const gone = fromThe("rank-stale-spec");
    const { container } = show(gone, { notUpdated: true, repairs: repairsFor(gone, stale, NO_EDITS), nameOf: () => null });

    expect(sent).toEqual(["syn-p0021", "syn-p9999"]);
    expect(sent.filter((id) => JSON.stringify(gone).includes(id))).toEqual([]);
    expect(sent.filter((id) => container.innerHTML.includes(id))).toEqual([]);
    expect(container.innerHTML.includes(CANARY)).toBe(false);
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

describe("how a failure is drawn", () => {
  const RULES = rulesOf(readFileSync(path.join(__dirname, "ErrorBlock.module.css"), "utf8"));
  const FORCED = /forced-colors:\s*active/;
  const DRAWN = RULES.filter((rule) => !FORCED.test(rule.under ?? ""));
  const setsOf = (selector: string) => new Map(DRAWN.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));
  const TOKENS = asWritten();
  /** The picture a button is drawn with, as the page names it on its face. */
  const drawnWith = (button: HTMLElement) =>
    /\/art\/([a-z0-9-]+)\.png/.exec((button.firstElementChild as HTMLElement).style.getPropertyValue("--art"))?.[1] ?? "";

  test("test_it_is_cream_inside_a_rule_of_ink_with_an_edge_of_poppy_and_its_words_are_in_ink", () => {
    const block = setsOf(".error");

    expect([block.get("background"), block.get("border"), block.get("color")]).toEqual([
      "var(--bg)",
      "var(--edge) solid var(--border)",
      "var(--text)",
    ]);
    expect(block.get("box-shadow")).toBe("inset var(--band) 0 0 var(--error-edge)");
    expect([TOKENS["--error-edge"], TOKENS["--error"]]).toEqual(["var(--poppy)", "var(--ink)"]);
    // Poppy is an edge and never words: on cream it cannot be read.
    const words = DRAWN.flatMap((rule) => (rule.sets.has("color") ? [rule.sets.get("color")] : []));
    expect(words.sort()).toEqual(["var(--error)", "var(--muted)", "var(--text)"]);
  });

  test("test_it_is_plain_and_flat", () => {
    const thrown = DRAWN.filter((rule) => rule.sets.has("box-shadow") && !/^inset /.test(rule.sets.get("box-shadow") ?? ""));

    expect(thrown.map((rule) => rule.selector)).toEqual([]);
    expect(DRAWN.filter((rule) => rule.sets.has("border-image") || rule.sets.has("border-radius")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_what_can_be_done_is_drawn_as_buttons_and_none_is_the_button_that_matters_most", () => {
    const failure = fromThe("rank-stale-spec");
    show(failure, { repairs: repairsFor(failure, stale, NO_EDITS), nameOf: () => null });

    const drawn = Object.fromEntries(screen.getAllByRole("button").map((button) => [button.textContent, drawnWith(button)]));

    expect(drawn).toEqual({
      [NOTICE.takeOut(NOTICE.thePlace)]: "ui-button",
      [PROMPT.tryAgain]: "ui-button",
      // It keeps nothing of the search, and is drawn as what takes away is drawn.
      [PROMPT.startAgain]: "ui-button-stop",
    });
    for (const button of screen.getAllByRole("button")) {
      expect(button.tagName).toBe("BUTTON");
      expect(button).toHaveAttribute("type", "button");
      expect(button).toHaveClass("target");
      // A button that holds no state says none.
      expect(button).not.toHaveAttribute("aria-pressed");
    }
  });

  test("test_what_a_repair_takes_out_is_a_name_the_service_gives_and_is_set_to_be_read", () => {
    const failure = fromThe("rank-stale-spec");
    const long = "Saint Bartholomew the Less Hospital, West Smithfield";
    show(failure, { repairs: repairsFor(failure, stale, NO_EDITS), nameOf: () => long });

    const repair = screen.getByRole("button", { name: NOTICE.takeOut(long) });

    expect(repair.querySelector("[data-reads='true']")?.textContent).toBe(NOTICE.takeOut(long));
    expect(screen.getByRole("button", { name: PROMPT.tryAgain }).querySelector("[data-reads='true']")).toBeNull();
  });

  test("test_the_id_of_a_request_is_broken_where_it_must_be_so_that_the_page_is_never_wider_for_it", () => {
    expect(setsOf(".request").get("overflow-wrap")).toBe("anywhere");
  });
});
