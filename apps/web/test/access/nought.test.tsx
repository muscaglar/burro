/**
 * A thing that counts, brought down to nought by keyboard: its slider goes when the answer
 * comes, and in the box a chip opens the chip goes with it. The focus must not go with
 * either: it is never left on nothing (docs/design/web.md, section 9, check 5).
 *
 * Seen in a browser, at 1440 by 900 and at 390 by 844, in Deep search and under "Refine
 * search": one press of the minus of a thing that stands at 5 left the focus on the page
 * as a whole, and the next press of Space moved the page by a screen.
 */

import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";

import { SETTLE_MS } from "@/components/WeightSlider/WeightSlider";
import { FEATURES, SETTINGS, SLIDER } from "@/content/settings";
import { recordedAnswer, responseFrom } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { setOnline } from "../support/api";
import { openSearch, search, settingsAt, settled, theSettings } from "../support/search";
import { focusGoesOnlyToWhatIsDrawn, theFocusIsOnWhatIsDrawn } from "./drawn";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

type User = Awaited<ReturnType<typeof openSearch>>["user"];

const ranked = recordedAnswer("rank", "rank-first");
const first = ranked.body.data;
const sentEdits = (body: unknown) => (body as { operations: Operations }).operations;
/** The first ranking, as the service would answer it for a search that holds this. */
const rankedWith = (holds: Partial<PreferenceSpec>) => () =>
  responseFrom({
    ...ranked,
    body: { ...ranked.body, data: { ...ranked.body.data, spec: { ...ranked.body.data.spec, ...holds } } },
  });
/** The search as it was first ranked, with one thing of it brought to nought. */
const atNought = (featureId: string): Partial<PreferenceSpec> => ({
  weights: first.spec.weights.map((weight) =>
    weight.feature_id === featureId ? { ...weight, weight: 0, provenance: "ui_edit" as const } : weight,
  ),
});

beforeEach(() => {
  setOnline(true);
  focusGoesOnlyToWhatIsDrawn();
});

async function tabTo(user: User, wanted: () => Element | null) {
  for (let presses = 0; presses < 400; presses += 1) {
    if (document.activeElement !== null && document.activeElement === wanted()) return presses;
    await user.tab();
  }
  throw new Error("Tab never reached it.");
}

/** Lets the moment pass after which a slider sends what it was set to. */
const aMoment = () => act(async () => void (await new Promise((resolve) => setTimeout(resolve, SETTLE_MS + 30))));

describe("the focus, when a thing that counts is brought to nought", () => {
  const AIR = "Cleaner air";
  const theSwitch = () => within(theSettings()).getByRole("switch", { name: AIR });
  const minus = () => within(theSettings()).queryByRole("button", { name: SLIDER.less(FEATURES.weight(AIR)) });
  const field = () => within(theSettings()).queryByRole("textbox", { name: SLIDER.number(FEATURES.weight(AIR)) });
  const slider = () => within(theSettings()).queryByRole("slider", { name: FEATURES.weight(AIR) });

  test("test_the_minus_of_a_slider_pressed_down_to_nought_hands_the_focus_to_the_switch_of_its_thing", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settingsAt(user, SETTINGS.airAndNoise);
    expect(theSwitch()).toBeChecked();
    const answer = api.hold("rank", rankedWith(atNought("air_no2")));
    await tabTo(user, minus);

    // It stands at 5, and a press takes a step of 10: one press brings it to nought.
    await user.keyboard("{Enter}");
    await aMoment();
    await waitFor(() => expect(answer.waiting()).toBe(1));
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.featureWeight("air_no2", 0));
    answer.release();
    await settled();

    expect(minus()).toBeNull();
    expect(slider()).toBeNull();
    expect(theSwitch()).not.toBeChecked();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    expect(theSwitch()).toHaveFocus();
  });

  test("test_the_field_of_a_slider_set_to_nought_hands_the_focus_to_the_switch_of_its_thing", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settingsAt(user, SETTINGS.airAndNoise);
    const answer = api.hold("rank", rankedWith(atNought("air_no2")));
    await tabTo(user, field);

    await user.keyboard("{Control>}a{/Control}0{Enter}");
    await waitFor(() => expect(answer.waiting()).toBe(1));
    answer.release();
    await settled();

    expect(field()).toBeNull();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    expect(theSwitch()).toHaveFocus();
  });

  test("test_the_slider_itself_brought_to_nought_hands_the_focus_to_the_switch_of_its_thing", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settingsAt(user, SETTINGS.airAndNoise);
    const answer = api.hold("rank", rankedWith(atNought("air_no2")));
    await tabTo(user, slider);

    fireEvent.change(slider() as HTMLElement, { target: { value: "0" } });
    await aMoment();
    await waitFor(() => expect(answer.waiting()).toBe(1));
    answer.release();
    await settled();

    expect(slider()).toBeNull();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    expect(theSwitch()).toHaveFocus();
  });

  test("test_a_slider_brought_to_nought_with_the_focus_elsewhere_moves_no_focus", async () => {
    const { user, api } = await openSearch();
    await search(user);
    await settingsAt(user, SETTINGS.airAndNoise);
    api.on("rank", rankedWith(atNought("air_no2")));
    const bar = within(theSettings()).getByRole("button", { name: SETTINGS.airAndNoise });

    // As by a pointer that set it, and then pressed elsewhere before the answer came.
    fireEvent.change(slider() as HTMLElement, { target: { value: "0" } });
    bar.focus();
    await aMoment();
    await settled();

    expect(slider()).toBeNull();
    expect(bar).toHaveFocus();
  });
});

describe("the focus, when the box a chip opens brings its thing to nought", () => {
  const chip = (name: RegExp) => screen.queryByRole("button", { name });

  test("test_a_chip_that_goes_as_its_slider_reaches_nought_hands_the_focus_to_the_chip_beside_it", async () => {
    const { user, api } = await openSearch();
    await search(user);
    const answer = api.hold("rank", rankedWith({ tags: first.spec.tags.filter((tag) => tag.tag_id !== "leafy") }));
    await tabTo(user, () => chip(/^Leafy/));
    await user.keyboard("{Enter}");
    const slider = () => screen.queryByRole("slider", { name: "Leafy" });
    await tabTo(user, slider);

    fireEvent.change(slider() as HTMLElement, { target: { value: "0" } });
    await aMoment();
    await waitFor(() => expect(answer.waiting()).toBe(1));
    expect(sentEdits(api.lastCallTo("rank").body)).toEqual(edits.tagOff("leafy"));
    answer.release();
    await settled();

    expect(chip(/^Leafy/)).toBeNull();
    expect(theFocusIsOnWhatIsDrawn()).toBe(true);
    expect(chip(/^Quiet streets/)).toHaveFocus();
  });
});
