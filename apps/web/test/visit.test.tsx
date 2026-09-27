/**
 * One person's whole visit, as a person makes it: a look at both ways in, a
 * first search, a second sentence, a control, a place named in part, the
 * notice, a sentence that holds nothing, an area's page, a comparison, a link
 * made and opened, a search the model did not answer, and a search begun at
 * the shelf: a word added, a scale turned, and a sentence that is no plain
 * list, of which Burro takes what it noticed.
 *
 * Every other test answers the website from a recording whatever it sends.
 * This one answers a request only if it is, to the letter, a request the
 * service was sent when the visit was recorded (`record_the_visit` in
 * `test/record.py`), where each request is made of the answer before it. So
 * it holds the website to what the service takes, and what it shows to what
 * the service said of that very search.
 *
 * The website asks nothing since the founder's second review: what Burro
 * noticed it takes of itself, and a name that several places bear is the first
 * of them. The visit was recorded while a person chose: the second of the
 * places, and fewer pubs. It was recorded again as the website now makes it,
 * so the whole visit is held. Beside it stands a plain test of its first steps.
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";

import AreaPage from "@/app/[city]/[area]/page";
import { CompareView } from "@/components/CompareTable/CompareView";
import { SearchApp } from "@/components/SearchApp/SearchApp";
import { SharedSearch } from "@/components/SharedSearch/SharedSearch";
import { Shell } from "@/components/Shell/Shell";
import { COMPARE, COMPARE_TABLE, TRAY } from "@/content/compare";
import { CHIPS, LEFT_OUT, NOTICE, RESULTS, SHELF, SOURCE, STATUS, UNMET } from "@/content/search";
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
  helper,
  meta,
  promptBox,
  results,
  settingsAt,
  settled,
  theSettingsIfAny,
  way,
  whatRefines,
  workingOf,
} from "./support/search";
import { stepOfTheVisit, stepsOfTheVisit, visitApi, type VisitApi } from "./support/visit";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

/** The group of the settings that holds a family of vibes, by the name the service gives the family. */
const groupOf = (family: string) => meta.data.families.find((one) => one.family === family)?.label ?? "";

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

/** The part of a result that one of its headings heads. */
const partUnder = (card: HTMLElement, heading: string) =>
  within(card).getByRole("heading", { name: heading }).parentElement as HTMLElement;
/** What a card says under "Trade-off", which is what a card says of what the service wrote of its area. */
const tradeOffOf = (card: HTMLElement) =>
  partUnder(card, RESULTS.tradeOffTitle).textContent?.slice(RESULTS.tradeOffTitle.length);
/** What the working of a card says under "Why it fits": each line of it, as it is written. */
const reasonsOf = (card: HTMLElement) =>
  within(partUnder(card, RESULTS.reasonsTitle))
    .getAllByRole("listitem")
    .map((reason) => reason.textContent);

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

  /** A look at both ways in, a first sentence, a second, and a control. It answers with the last ranking. */
  async function theFirstDay(api: VisitApi, user: ReturnType<typeof userEvent.setup>): Promise<RankData> {
    // A look at the second way in and at a group of its settings, and back to the first:
    // nothing is set, and nothing is sent.
    await settingsAt(user, SETTINGS.airAndNoise);
    await way(user, "quick");
    expect(api.unanswered).toEqual([]);
    expect(api.unused()).toEqual(stepsOfTheVisit().map((step) => step.scenario));

    // A first sentence, sent with the defaults the page opened on.
    const first = answerOf<RankData>("first-rank");
    await say(user, "first");
    expect(status().join(" ")).toContain(STATUS.ranked(first.scores.length, nameOf(first.ranked[0]?.area_id)));
    // Every chip and every result, which stay opened out for the rest of the search.
    await everyChip(user);
    await everyResult(user);
    expect(results()).toHaveLength(first.ranked.length);
    expect(results()[0]).toHaveTextContent(RESULTS.fitOf(fitOf(first.ranked[0]?.score ?? 0)));
    const written = answerOf<ExplanationsData>("first-reasons").explanations;
    expect(written.map((one) => one.area_id)).toEqual(first.ranked.slice(0, 5).map((area) => area.area_id));
    for (const [at, explanation] of written.entries()) {
      // The trade-off is in the answer, and no reason is: a card says why it fits in its working.
      const card = results()[at] as HTMLElement;
      expect([at, tradeOffOf(card)]).toEqual([at, explanation.trade_off?.text ?? RESULTS.noTradeOff]);
      expect([at, explanation.reasons.some((reason) => card.textContent?.includes(reason.text))]).toEqual([at, false]);
      // Every reason is in the working of the result, in the order the service gave them,
      // and each ends in the key of its source.
      expect((await workingOf(user, nameOf(explanation.area_id))) === card).toBe(true);
      expect(explanation.reasons.length).toBeGreaterThan(0);
      expect(reasonsOf(card)).toEqual(
        explanation.reasons.map(
          (reason) => `${reason.text}${reason.origin === "model" ? RESULTS.byModel : ""}${SOURCE.button}`,
        ),
      );
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
    await settingsAt(user, groupOf("pace_food"), FEATURES.madeOfName("Going out"));
    expect(screen.getByRole("switch", { name: highStreet })).not.toBeChecked();
    // The settings are folded again, over the answer, by what opened them.
    await user.click(whatRefines() as HTMLElement);
    expect(whatRefines()).toHaveAttribute("aria-expanded", "false");
    expect(theSettingsIfAny()).toBeNull();
    return firm;
  }

  /** Another day: a model reads and does not answer, and the rules read the words in its place. */
  async function theDayAModelDidNotAnswer(user: ReturnType<typeof userEvent.setup>): Promise<void> {
    // What the rules noticed is taken at once, and ranked: it never waits on a model. The
    // model's answer does not come, the rules answer in its place with what they had
    // noticed, and nothing is taken or ranked a second time.
    const slow = answerOf<InterpretData>("slow");
    await say(user, "slow");
    expect(answerOf<InterpretData>("slow-at-once")).toMatchObject({ model_pending: true, degraded: false });
    expect(slow).toMatchObject({ degraded: true, interpreter: "rule", applied: [] });
    // The line is said once the model's answer has not come, which is a moment after the rules'.
    await waitFor(() => expect(status()).toContain(NOTICE.degraded));
    await settled();
    const [water] = slow.suggestions;
    expect(screen.queryByRole("region", { name: "Choose what to add" })).toBeNull();
    expect(chip(water?.label ?? "no such thing")).toBeInTheDocument();
    expect(results()[0]).toHaveTextContent(nameOf(answerOf<RankData>("slow-rank").ranked[0]?.area_id));
  }

  /** Another day again, begun at the shelf: a word added, and its scale turned. It answers with the last ranking. */
  async function theDayBegunAtTheShelf(user: ReturnType<typeof userEvent.setup>): Promise<RankData> {
    // The shelf is behind a helper, and opening one sends nothing.
    await helper(user, "word");
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
    return calm;
  }

  test("test_every_step_the_recording_answers_today_is_a_request_the_website_makes_and_what_is_shown_is_its_answer", async () => {
    // Today's behaviour, against the visit as it was recorded: every step of it that the
    // website still makes as it was recorded. When the whole visit under this passes, this
    // test goes: it holds nothing the whole visit does not.
    const api = visitApi();
    const user = userEvent.setup({ delay: null });
    const view = render(inShell(searchPage(api)));
    await arrived();

    await theFirstDay(api, user);
    view.unmount();
    const another = render(inShell(searchPage(api)));
    await arrived();
    await theDayAModelDidNotAnswer(user);
    another.unmount();
    render(inShell(searchPage(api)));
    await arrived();
    await theDayBegunAtTheShelf(user);

    // Nothing was sent that the service was not sent when the visit was recorded. And
    // every step of these days was asked for: what is left is what a person chose where
    // the website now asks nothing, and all that was made of the search they chose.
    expect(api.unanswered).toEqual([]);
    const walked = /^visit\/\d+-(first|second|firm|slow|shelf|turned)(-at-once|-rank|-reasons)?$/;
    expect(stepsOfTheVisit().filter((step) => walked.test(step.scenario))).toHaveLength(16);
    expect(api.unused().filter((step) => walked.test(step))).toEqual([]);
  }, 120_000);

  // The visit is recorded as the website makes it: it takes the first place the service
  // gave and what Burro noticed, and asks nothing.
  test("test_everything_a_visit_sends_is_a_request_the_service_answered_and_what_is_shown_is_its_answer", async () => {
    const api = visitApi();
    const user = userEvent.setup({ delay: null });
    const view = render(inShell(searchPage(api)));
    await arrived();

    const firm = await theFirstDay(api, user);
    const highStreet = plainNameOf("highstreet_access");

    // A place named in part. Nothing is asked: the journey is to the first of the places
    // the service gave, and its chip says that the place was assumed.
    const asked = answerOf<InterpretData>("place");
    await say(user, "place");
    const [taken] = asked.clarify[0]?.options ?? [];
    expect(asked.clarify[0]?.options.length).toBeGreaterThan(1);
    expect(document.body.textContent).not.toMatch(/Which (place|area) did you mean/);
    const answered = answerOf<RankData>("answered-rank");
    expect(answered.spec.commutes).toHaveLength(2);
    expect(answered.spec.commutes.map((journey) => journey.place_id)).toContain(taken?.id);
    expect(firm.spec.commutes).toHaveLength(1);
    expect(chip(taken?.name ?? "no place")).toHaveTextContent(CHIPS.assumed);
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
    await user.click(screen.getByRole("button", { name: COMPARE.addNamed(nameOf(one)) }));
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
    await theDayAModelDidNotAnswer(user);

    // Another day again, begun at the shelf: a word of it added, with nothing typed.
    another.unmount();
    render(inShell(searchPage(api)));
    await arrived();
    const calm = await theDayBegunAtTheShelf(user);

    // A sentence that is not plain. The service applies nothing of it, and returns what it
    // noticed: Burro takes what the words give the way of, and the areas are ranked again.
    // Nothing is offered.
    const noticed = answerOf<InterpretData>("noticed");
    await say(user, "noticed");
    expect(noticed.status).toBe("suggest");
    expect(noticed.spec).toEqual(calm.spec);
    expect(noticed.suggestions.map((one) => [one.target, one.only_by_choice])).toEqual([
      ["tag:young_professionals", true],
      ["tag:pace", false],
      ["feature:station_walk", false],
    ]);
    expect(screen.queryByRole("region", { name: "Choose what to add" })).toBeNull();
    const chosen = answerOf<RankData>("chosen-rank");
    expect(results()[0]).toHaveTextContent(nameOf(chosen.ranked[0]?.area_id));
    // What counts who lived somewhere waits for the person: it is not taken, no chip is
    // drawn of it, and the line of what was left out names it. "Lively" turns the scale
    // that was turned to its calm end, and the station is taken as it was said.
    expect(chosen.spec.tags.map((tag) => [tag.tag_id, tag.toward])).toEqual([["pace", "high"]]);
    expect(screen.queryByRole("button", { name: new RegExp(`^${noticed.suggestions[0]?.label}`) })).toBeNull();
    expect(screen.getByRole("status", { name: LEFT_OUT.title }).querySelector("summary")?.textContent).toBe(
      `${LEFT_OUT.title}: ${noticed.suggestions[0]?.label}`,
    );
    expect(chip(plainNameOf("station_walk"))).not.toHaveTextContent(CHIPS.assumed);

    // Nothing was sent that the service was not sent when the visit was recorded,
    // and nothing was recorded that the website does not send.
    expect(api.unanswered).toEqual([]);
    expect(api.unused()).toEqual([]);
  }, 120_000);
});
