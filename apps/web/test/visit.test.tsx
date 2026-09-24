/**
 * One person's whole visit, as a person makes it: a first search, a second
 * sentence, a control, a question answered, the notice, a sentence that holds
 * nothing, an area's page, a comparison, a link made and opened, and a search
 * the model did not answer.
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
import { CHIPS, CLARIFY, NOTICE, RESULTS, STATUS, UNMET } from "@/content/search";
import { JOURNEY, SETTINGS } from "@/content/settings";
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
import { areas, arrived, meta, promptBox, results, settled } from "./support/search";
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
const searchPage = (api: VisitApi) => <SearchApp meta={meta.data} areas={areas} client={api.client} />;

async function say(user: ReturnType<typeof userEvent.setup>, name: string) {
  await user.clear(promptBox());
  await user.type(promptBox(), sentenceOf(name));
  await user.keyboard("{Enter}");
  await settled();
}

/** The first sentence of each of the first five cards, which is where the area is. */
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
    expect(results()).toHaveLength(first.ranked.length);
    expect(results()[0]).toHaveTextContent(RESULTS.fitOf(fitOf(first.ranked[0]?.score ?? 0)));
    for (const [at, explanation] of answerOf<ExplanationsData>("first-reasons").explanations.entries()) {
      for (const reason of explanation.reasons) expect(firstReasons()[at]).toContain(reason.text);
    }

    // A second sentence: one thing more, and one taken off.
    const second = answerOf<InterpretData>("second");
    await say(user, "second");
    const takenOff = second.spec.weights.filter((weight) => weight.weight === 0);
    expect(takenOff.map((weight) => weight.feature_id)).toEqual(["highstreet_access"]);
    const highStreet = meta.data.features.find((feature) => feature.feature_id === "highstreet_access")?.label ?? "";
    expect(chip(highStreet)).toHaveTextContent(CHIPS.off);
    expect(screen.queryByRole("button", { name: `${CHIPS.remove}: ${highStreet}` })).toBeNull();
    expect(results()[0]).toHaveTextContent(nameOf(answerOf<RankData>("second-rank").ranked[0]?.area_id));

    // A control: the journey made a firm limit.
    const firm = answerOf<RankData>("firm-rank");
    await user.click(screen.getByRole("button", { name: SETTINGS.title }));
    await user.click(
      within(screen.getByRole("group", { name: JOURNEY.place("Cindermoor Works") })).getByRole("checkbox", {
        name: JOURNEY.firm,
      }),
    );
    await settled();
    expect(firm.filtered.length).toBeGreaterThan(0);
    expect(results()).toHaveLength(firm.ranked.length);
    expect(chip("Cindermoor Works")).toHaveTextContent(CHIPS.firm);
    // The switch of what was taken off is off, and stays off.
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
    expect(chip("Walk to the nearest park")).toBeInTheDocument();
    const last = answerOf<RankData>("people-rank");
    expect(results()[0]).toHaveTextContent(nameOf(last.ranked[0]?.area_id));

    // A sentence with nothing in it to read. The results stay.
    await say(user, "unread");
    expect(status()).toContain(NOTICE.nothingRead);
    expect(screen.queryByText(UNMET.other)).toBeNull();
    expect(results()).toHaveLength(last.ranked.length);

    // The second result is chosen from the list, and the first from its own page.
    const [one, two] = [last.ranked[0]?.area_id, last.ranked[1]?.area_id];
    await user.click(within(results()[1] as HTMLElement).getByRole("button", { name: COMPARE.add(nameOf(two)) }));
    view.rerender(inShell(await AreaPage({ params: Promise.resolve({ city: "synthetic", area: slugOf(one) }) })));
    await arrived();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(nameOf(one));
    expect(screen.getByRole("region", { name: BANNER.label })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: COMPARE.add(nameOf(one)) }));
    const go = screen.getByRole("link", { name: TRAY.go(2) });
    expect(go).toHaveAttribute("href", `/compare?a=${slugOf(two)}&a=${slugOf(one)}`);

    // The comparison, on the search as it stands.
    const compared = answerOf<CompareData>("compare");
    view.rerender(
      inShell(
        <CompareView
          chosen={chosenFrom([slugOf(two), slugOf(one)], areas).chosen}
          defaults={meta.data.defaults}
          client={api.client}
        />,
      ),
    );
    await arrived();
    await settled();
    expect(screen.getByRole("main")).toHaveTextContent(COMPARE.fromSearch);
    const rows = within(screen.getByRole("table", { name: COMPARE_TABLE.caption })).getAllByRole("rowheader");
    expect(rows).toHaveLength(compared.rows.length);
    // What was taken off counts for nothing, so it is no row of the comparison.
    expect(compared.rows.map((row) => row.component)).not.toContain("feature:highstreet_access");
    expect(screen.getByRole("main")).toHaveTextContent(
      COMPARE_TABLE.standing(1, fitOf(last.ranked[0]?.score ?? 0)),
    );

    // Back to the search, which is as it was, and a link made of it.
    view.rerender(inShell(searchPage(api)));
    await settled();
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
    expect(results()).toHaveLength(opened.ranked.length);
    expect(results()[0]).toHaveTextContent(nameOf(opened.ranked[0]?.area_id));
    expect(chip(highStreet)).toHaveTextContent(CHIPS.off);

    // Another day: the model does not answer, and the rules read the words in its place.
    tab.unmount();
    window.history.replaceState(null, "", "/");
    render(inShell(searchPage(api)));
    await arrived();
    const slow = answerOf<InterpretData>("slow");
    await say(user, "slow");
    expect(slow).toMatchObject({ degraded: true, interpreter: "rule" });
    expect(status()).toContain(NOTICE.degraded);
    expect(results()[0]).toHaveTextContent(nameOf(answerOf<RankData>("slow-rank").ranked[0]?.area_id));

    // Nothing was sent that the service was not sent when the visit was recorded,
    // and nothing was recorded that the website does not send.
    expect(api.unanswered).toEqual([]);
    expect(api.unused()).toEqual([]);
  }, 120_000);
});
