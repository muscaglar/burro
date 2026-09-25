/**
 * One person's whole visit, as a person makes it: a first search, a second
 * sentence, a control, a question answered, the notice, a sentence that holds
 * nothing, an area's page, a comparison, a link made and opened, a search
 * the model did not answer, and a search begun at the shelf: a word added, a
 * scale turned, and one of the things the reader noticed chosen.
 *
 * Every other test answers the website from a recording whatever it sends.
 * This one answers a request only if it is, to the letter, a request the
 * service was sent when the visit was recorded (`record_the_visit` in
 * `test/record.py`), where each request is made of the answer before it. So
 * it holds the website to what the service takes, and what it shows to what
 * the service said of that very search.
 */

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";

import AreaPage from "@/app/[city]/[area]/page";
import { CompareView } from "@/components/CompareTable/CompareView";
import { SearchApp } from "@/components/SearchApp/SearchApp";
import { SharedSearch } from "@/components/SharedSearch/SharedSearch";
import { Shell } from "@/components/Shell/Shell";
import { COMPARE, COMPARE_TABLE, TRAY } from "@/content/compare";
import { CHIPS, CLARIFY, NOTICE, RESULTS, SHELF, STATUS, SUGGEST, UNMET } from "@/content/search";
import { FEATURES, JOURNEY, SETTINGS } from "@/content/settings";
import { SHARE, SHARED } from "@/content/share";
import { BANNER } from "@/content/site";
import type {
  CompareData,
  ExplanationsData,
  InterpretBody,
  InterpretData,
  RankData,
  ShareCreated,
  ShareData,
} from "@/lib/api/schema";
import { chosenFrom } from "@/lib/compare/list";
import { fitOf } from "@/lib/map/fill";

import { setOnline } from "./support/api";
import {
  areas,
  arrived,
  bands,
  everyChip,
  everyResult,
  meta,
  promptBox,
  results,
  settingsAt,
  settled,
  workingOf,
} from "./support/search";
import { stepOfTheVisit, stepsOfTheVisit, visitApi, type VisitApi } from "./support/visit";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

interface Enveloped<Data> {
  readonly data: Data;
}
const answerOf = <Data,>(name: string) => stepOfTheVisit<Enveloped<Data>>(name).body.data;
const sentenceOf = (name: string) => (stepOfTheVisit(name).request.body as InterpretBody).text;
const nameOf = (areaId: string | undefined) => areas.find((area) => area.area_id === areaId)?.name ?? "no such area";
const slugOf = (areaId: string | undefined) => areas.find((area) => area.area_id === areaId)?.slug ?? "";

const status = () => screen.getAllByRole("status").map((line) => line.textContent ?? "");
const chip = (name: string) => screen.getByRole("button", { name: new RegExp(`^${name}`) });
const inShell = (page: ReactElement) => <Shell meta={meta.meta}>{page}</Shell>;
const searchPage = (api: VisitApi) => (
  <SearchApp meta={meta.data} areas={areas} bands={bands} client={api.client} />
);
/** The plain name of a feature, which is what a chip and a switch are named by. */
const plainNameOf = (featureId: string) =>
  meta.data.features.find((feature) => feature.feature_id === featureId)?.short_label ?? "";

async function say(user: ReturnType<typeof userEvent.setup>, name: string) {
  await user.clear(promptBox());
  await user.type(promptBox(), sentenceOf(name));
  await user.keyboard("{Enter}");
  await settled();
}

/** The first reason of each of the first five cards, which is in the answer. */
const firstReasons = () =>
  results()
    .slice(0, 5)
    .map((card) => within(card).getByRole("heading", { name: RESULTS.reasonsTitle }).parentElement?.textContent ?? "");

beforeEach(() => {
  setOnline(true);
  window.history.replaceState(null, "", "/");
});

describe("one person's whole visit", () => {
  test("test_the_visit_was_recorded_step_by_step_from_the_service", () => {
    const steps = stepsOfTheVisit();

    expect(steps.length).toBeGreaterThan(20);
    expect(steps.filter((step) => !step.captured)).toEqual([]);
    // The service took every request of the visit: none was refused.
    expect(steps.filter((step) => step.status !== 200).map((step) => step.scenario)).toEqual([]);
  });

  test("test_everything_a_visit_sends_is_a_request_the_service_answered_and_what_is_shown_is_its_answer", async () => {
    const api = visitApi();
    const user = userEvent.setup({ delay: null });
    const view = render(inShell(searchPage(api)));
    await arrived();

    // A first sentence, sent with the defaults the page opened on.
    const first = answerOf<RankData>("first-rank");
    await say(user, "first");
    expect(status().join(" ")).toContain(STATUS.ranked(first.scores.length, nameOf(first.ranked[0]?.area_id)));
    // Every chip and every result, which stay opened out for the rest of the search.
    await everyChip(user);
    await everyResult(user);
    expect(results()).toHaveLength(first.ranked.length);
    expect(results()[0]).toHaveTextContent(RESULTS.fitOf(fitOf(first.ranked[0]?.score ?? 0)));
    for (const [at, explanation] of answerOf<ExplanationsData>("first-reasons").explanations.entries()) {
      expect(firstReasons()[at]).toContain(explanation.reasons[0]?.text);
      // The other reasons are in the working of the result.
      const card = await workingOf(user, nameOf(explanation.area_id));
      for (const reason of explanation.reasons) expect(card.textContent?.includes(reason.text)).toBe(true);
    }

    // A second sentence: one thing more, and one taken off.
    const second = answerOf<InterpretData>("second");
    await say(user, "second");
    const takenOff = second.spec.weights.filter((weight) => weight.weight === 0);
    expect(takenOff.map((weight) => weight.feature_id)).toEqual(["highstreet_access"]);
    const highStreet = plainNameOf("highstreet_access");
    expect(chip(highStreet)).toHaveTextContent(CHIPS.off);
    expect(screen.queryByRole("button", { name: `${CHIPS.remove}: ${highStreet}` })).toBeNull();
    expect(results()[0]).toHaveTextContent(nameOf(answerOf<RankData>("second-rank").ranked[0]?.area_id));

    // A control: the journey made a firm limit.
    const firm = answerOf<RankData>("firm-rank");
    await settingsAt(user, SETTINGS.journeys);
    await user.click(
      within(screen.getByRole("group", { name: JOURNEY.place("Cindermoor Works") })).getByRole("checkbox", {
        name: JOURNEY.firm,
      }),
    );
    await settled();
    expect(firm.filtered.length).toBeGreaterThan(0);
    expect(results()).toHaveLength(firm.ranked.length);
    expect(chip("Cindermoor Works")).toHaveTextContent(CHIPS.firm);
    // The switch of what was taken off is off, and stays off. It is a part of the recipe of Going out.
    await settingsAt(user, "Pace and food", FEATURES.madeOfName("Going out"));
    expect(screen.getByRole("switch", { name: highStreet })).not.toBeChecked();
    await user.click(screen.getByRole("button", { name: SETTINGS.title }));

    // A place named in part: a question, and nothing ranked again until it is answered.
    const asked = answerOf<InterpretData>("place");
    await say(user, "place");
    const question = within(screen.getByRole("region", { name: CLARIFY.question }));
    expect(asked.clarify[0]?.options.map((option) => option.name)).toContain("Pellam Exchange");
    expect(results()).toHaveLength(firm.ranked.length);
    await user.click(question.getByRole("button", { name: /^Pellam Exchange/ }));
    await settled();
    const answered = answerOf<RankData>("answered-rank");
    expect(answered.spec.commutes).toHaveLength(2);
    expect(screen.queryByRole("region", { name: CLARIFY.question })).toBeNull();
    expect(chip("Pellam Exchange")).toBeInTheDocument();
    expect(results()[0]).toHaveTextContent(nameOf(answered.ranked[0]?.area_id));

    // Part of a sentence is about who lives somewhere: the API's one sentence, and the rest.
    const people = answerOf<InterpretData>("people");
    await say(user, "people");
    expect(people.notice).toBe("neutral_places");
    expect(status().filter((line) => line === people.notice_text)).toHaveLength(1);
    expect(chip(plainNameOf("park_proximity"))).toBeInTheDocument();
    const last = answerOf<RankData>("people-rank");
    expect(results()[0]).toHaveTextContent(nameOf(last.ranked[0]?.area_id));

    // A sentence with nothing in it to read. The results stay.
    await say(user, "unread");
    expect(status()).toContain(NOTICE.nothingRead);
    expect(screen.queryByText(UNMET.other)).toBeNull();
    expect(results()).toHaveLength(last.ranked.length);

    // The second result is chosen from the list, and the first from its own page.
    const [one, two] = [last.ranked[0]?.area_id, last.ranked[1]?.area_id];
    await user.click(within(results()[1] as HTMLElement).getByRole("button", { name: COMPARE.addNamed(nameOf(two)) }));
    // "More like this" leads to the part of the area's own page that lists what is like it.
    expect(within(results()[0] as HTMLElement).getByRole("link", { name: RESULTS.moreLikeOf(nameOf(one)) })).toHaveAttribute(
      "href",
      `/synthetic/${slugOf(one)}#alike`,
    );
    view.rerender(inShell(await AreaPage({ params: Promise.resolve({ city: "synthetic", area: slugOf(one) }) })));
    await arrived();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(nameOf(one));
    expect(screen.getByRole("region", { name: BANNER.label })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: COMPARE.add(nameOf(one)) }));
    // The way to the comparison is beside the button that was pressed, and in the tray at the
    // foot of the screen. Both lead to the same two areas.
    const ways = screen.getAllByRole("link", { name: TRAY.go(2) });
    expect(ways).toHaveLength(2);
    for (const go of ways) expect(go).toHaveAttribute("href", `/compare?a=${slugOf(two)}&a=${slugOf(one)}`);

    // The comparison, on the search as it stands.
    const compared = answerOf<CompareData>("compare");
    view.rerender(
      inShell(
        <CompareView
          chosen={chosenFrom([slugOf(two), slugOf(one)], areas).chosen}
          defaults={meta.data.defaults} tags={meta.data.tags}
          client={api.client}
        />,
      ),
    );
    await arrived();
    await settled();
    expect(screen.getByRole("main")).toHaveTextContent(COMPARE.fromSearch);
    const rows = within(screen.getByRole("table", { name: COMPARE_TABLE.caption })).getAllByRole("rowheader");
    // One row for each thing that counts, as the service sent them. It sent one for each
    // place the journeys are to, and every area is timed to the place of its row.
    const timedTo = compared.rows.flatMap((row) => (row.place === null ? [] : [row.place.name]));
    expect(timedTo).toHaveLength(2);
    expect(new Set(timedTo).size).toBe(2);
    expect(rows).toHaveLength(compared.rows.length);
    for (const place of timedTo) {
      expect(rows.filter((row) => row.textContent?.includes(COMPARE_TABLE.journeys.to(place)))).toHaveLength(1);
    }
    // What was taken off counts for nothing, so it is no row of the comparison.
    expect(compared.rows.map((row) => row.component)).not.toContain("feature:highstreet_access");
    expect(screen.getByRole("main")).toHaveTextContent(
      COMPARE_TABLE.standing(1, fitOf(last.ranked[0]?.score ?? 0)),
    );

    // Back to the search, which is as it was, and a link made of it.
    view.rerender(inShell(searchPage(api)));
    await settled();
    await everyResult(user);
    expect(results()).toHaveLength(last.ranked.length);
    const made = answerOf<ShareCreated>("share-made");
    await user.click(screen.getByRole("button", { name: SHARE.open }));
    await user.click(screen.getByRole("button", { name: SHARE.make }));
    await screen.findByText(SHARE.made);
    const link = screen.getByRole<HTMLInputElement>("textbox", { name: SHARE.link }).value;
    expect(link).toBe(`${window.location.origin}/s#${made.share_id}`);

    // The link opened, in a tab of its own.
    view.unmount();
    window.history.replaceState(null, "", "/s");
    window.location.hash = made.share_id;
    const tab = render(inShell(<SharedSearch meta={meta.data} areas={areas} client={api.client} />));
    await arrived();
    await settled();
    const opened = answerOf<ShareData>("share-opened");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(SHARED.title);
    await everyChip(user);
    await everyResult(user);
    expect(results()).toHaveLength(opened.ranked.length);
    expect(results()[0]).toHaveTextContent(nameOf(opened.ranked[0]?.area_id));
    expect(chip(highStreet)).toHaveTextContent(CHIPS.off);
    // The places of a share are shown by the names the answer gives them.
    for (const place of opened.places) expect(chip(place.name)).toBeInTheDocument();

    // Another day: the model does not answer, and the rules read the words in its place.
    tab.unmount();
    window.history.replaceState(null, "", "/");
    const another = render(inShell(searchPage(api)));
    await arrived();
    // A model reads, and does not answer. What the rules offer is on the page at once, and
    // stays when the model's answer does not come.
    const slow = answerOf<InterpretData>("slow");
    await say(user, "slow");
    expect(answerOf<InterpretData>("slow-at-once")).toMatchObject({ model_pending: true, degraded: false });
    expect(slow).toMatchObject({ degraded: true, interpreter: "rule", applied: [] });
    expect(status()).toContain(NOTICE.degraded);
    const water = slow.suggestions[0];
    await user.click(screen.getByRole("button", { name: SUGGEST.named("Add", water?.label ?? "") }));
    await settled();
    expect(results()[0]).toHaveTextContent(nameOf(answerOf<RankData>("slow-rank").ranked[0]?.area_id));

    // Another day again, begun at the shelf: a word of it added, with nothing typed.
    another.unmount();
    render(inShell(searchPage(api)));
    await arrived();
    const shelf = within(screen.getByRole("region", { name: SHELF.title }));
    await user.click(shelf.getByRole("button", { name: "lively" }));
    await user.click(screen.getByRole("button", { name: SHELF.add }));
    await settled();
    const lively = answerOf<RankData>("shelf-rank");
    expect(lively.spec.tags).toMatchObject([{ tag_id: "pace", toward: "high" }]);
    expect(chip(CHIPS.towards("Going out", "Buzzy"))).toBeInTheDocument();
    expect(results()[0]).toHaveTextContent(nameOf(lively.ranked[0]?.area_id));

    // The chip of the scale is turned: the other end, with the weight it had.
    await user.click(screen.getByRole("button", { name: CHIPS.turnTo("Going out", "Calm") }));
    await settled();
    const calm = answerOf<RankData>("turned-rank");
    expect(calm.spec.tags).toMatchObject([{ tag_id: "pace", toward: "low", weight: lively.spec.tags[0]?.weight }]);
    expect(chip(CHIPS.towards("Going out", "Calm"))).toBeInTheDocument();
    expect(results()[0]).toHaveTextContent(nameOf(calm.ranked[0]?.area_id));

    // A sentence that is not plain. Nothing of it is applied, and nothing is ranked again.
    const noticed = answerOf<InterpretData>("noticed");
    await say(user, "noticed");
    expect(noticed.status).toBe("suggest");
    expect(noticed.spec).toEqual(calm.spec);
    const offered = within(screen.getByRole("region", { name: SUGGEST.title }));
    // Each offer is named by what it would do, in the API's words.
    const told = offered.getAllByRole("group").map((thing) => thing.getAttribute("aria-labelledby") ?? "");
    expect(told.map((id) => document.getElementById(id)?.textContent)).toEqual(
      noticed.suggestions.map((one) => one.does),
    );
    expect(results()[0]).toHaveTextContent(nameOf(calm.ranked[0]?.area_id));

    // One of the things noticed is chosen: the edits the API gave with the choice.
    const fewer = noticed.suggestions[0]?.choices[1];
    await user.click(offered.getByRole("button", { name: fewer?.label }));
    await settled();
    const chosen = answerOf<RankData>("chosen-rank");
    expect(results()[0]).toHaveTextContent(nameOf(chosen.ranked[0]?.area_id));
    expect(chip(plainNameOf("venue_evening_per_homes"))).toBeInTheDocument();

    // Nothing was sent that the service was not sent when the visit was recorded,
    // and nothing was recorded that the website does not send.
    expect(api.unanswered).toEqual([]);
    expect(api.unused()).toEqual([]);
  }, 120_000);
});
