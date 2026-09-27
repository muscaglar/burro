import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DIMENSION, DIRECTION } from "@/content/labels";
import { FEATURES, SETTINGS, SLIDER, SWITCH } from "@/content/settings";
import { failed } from "@/lib/api/failure";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { cutOf } from "../kit/drawings";
import { SLIDER_STANDS, SLIDER_STANDS_ARE } from "./look";
import { SettingsPanel } from "./SettingsPanel";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
/** "Renting a 1 bed for about £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works", as it was ranked. */
const first = recordedAnswer("rank", "rank-first").body.data.spec;
/** The same, with recorded burglary and theft switched on, as the service answered the switch. */
const theftOn = recordedAnswer("rank", "rank-crime-switched-on").body.data.spec;
/** "nights out", as it was ranked: pubs and bars count, which may count either way. */
const nights = recordedAnswer("rank", "rank-nights-out").body.data.spec;
const NAMED = { "syn-p0021": "Cindermoor Works" } as const;
const STREETS = meta.families.find((one) => one.family === "streets_homes")?.label ?? "";
const GOING_OUT = meta.families.find((one) => one.family === "pace_food")?.label ?? "";

const THEFT = "Less recorded burglary and theft";
const VIOLENCE = "Less recorded violence and robbery";

function show(spec: PreferenceSpec = first) {
  const sent: Operations[] = [];
  const panel = (shown: PreferenceSpec, at: number) => (
    <SettingsPanel
      spec={shown}
      meta={meta}
      areas={areas}
      placeNames={NAMED}
      onEdit={(operations) => sent.push(operations)}
      onTenure={() => undefined}
      searchPlaces={() => Promise.resolve(failed("offline"))}
      onAddPlace={() => undefined}
      version={at}
      open
      onToggle={() => undefined}
      standing
    />
  );
  const view = render(panel(spec, 1));
  const user = userEvent.setup({ delay: null });
  const open = async (...names: string[]) => {
    for (const name of names) {
      const button = screen.getByRole("button", { name });
      if (button.getAttribute("aria-expanded") !== "true") await user.click(button);
    }
  };
  return { ...view, sent, user, open, again: (next: PreferenceSpec, at: number) => view.rerender(panel(next, at)) };
}

/** The switch of a thing, by the name of the thing. */
const theSwitch = (name: string) => screen.getByRole("switch", { name });
/** All that is set of a thing: its switch, and what the switch shows. */
const rowOf = (name: string) => theSwitch(name).closest("[role='group']") as HTMLElement;
/** What a switch says of itself in a word, for the eye. */
const wordOf = (name: string) => theSwitch(name).parentElement?.querySelector("[data-says]") ?? null;
/** The room of what a switch shows: its slider, and which way it counts where either can. */
const roomOf = (name: string) => rowOf(name).querySelector(".inner") as HTMLElement;
/** Everything in a part that takes a press, a key or the focus. */
const taking = (part: Element) =>
  [...part.querySelectorAll<HTMLElement>("a[href], button, input, select, textarea, [tabindex]")].filter(
    (one) => !(one as HTMLButtonElement).disabled && one.closest("fieldset:disabled") === null,
  );
/** How a part is made, by the class of each thing in it, in the order they stand: what a style sheet lays out. */
const madeAs = (part: Element): string[] =>
  [...part.children].flatMap((one) => [`${one.tagName.toLowerCase()}.${one.classList[0] ?? ""}`, ...madeAs(one).map((inside) => `  ${inside}`)]);

const CSS = readFileSync(path.join(__dirname, "SettingsPanel.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const ALL = rulesOf(CSS);
const STYLES = ALL.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
const setsOf = (selector: string) =>
  new Map(
    STYLES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) =>
      [...rule.sets].map(([property, value]): [string, string] => [property, value.replace(/\s+/g, " ")]),
    ),
  );
const served = (name: string) => `url("/art/${name}.png")`;

describe("a switch says whether it is on or off", () => {
  test("test_it_says_so_in_a_word_beside_its_lamp_which_is_on_or_off", async () => {
    // The founder: "it is unclear what the select state of the toggle is".
    const { open } = show();
    await open(SETTINGS.airAndNoise, DIMENSION.crime);

    expect([SWITCH.on, SWITCH.off]).toEqual(["On", "Off"]);
    expect(theSwitch("Cleaner air")).toBeChecked();
    expect(wordOf("Cleaner air")).toHaveTextContent(/^On$/);
    expect(wordOf("Cleaner air")).toHaveAttribute("data-says", "on");
    expect(theSwitch(THEFT)).not.toBeChecked();
    expect(wordOf(THEFT)).toHaveTextContent(/^Off$/);
    expect(wordOf(THEFT)).toHaveAttribute("data-says", "off");
  });

  test("test_every_switch_of_the_settings_says_the_word_that_is_so_of_it", async () => {
    const { open } = show();
    await open(...meta.families.map((one) => one.label), DIMENSION.brands, SETTINGS.airAndNoise, DIMENSION.crime);
    for (const tag of meta.tags) await open(FEATURES.madeOfName(tag.label));
    const switches = screen.getAllByRole("switch");

    expect(switches.length).toBeGreaterThan(80);
    for (const one of switches) {
      const word = one.parentElement?.querySelector("[data-says]");
      expect([one.getAttribute("aria-describedby") !== null, word?.textContent]).toEqual([
        true,
        (one as HTMLInputElement).checked ? SWITCH.on : SWITCH.off,
      ]);
    }
    // Some are on and some are off: both are seen.
    expect(new Set(switches.map((one) => (one as HTMLInputElement).checked))).toEqual(new Set([true, false]));
  });

  test("test_the_word_is_for_the_eye_and_whoever_hears_the_page_hears_it_of_the_switch_itself", async () => {
    const { open } = show();
    await open(DIMENSION.crime);

    // It is heard once: the switch is the browser's own, and says that it is off. Its name
    // is the name of the thing, which the word is no part of.
    expect(wordOf(THEFT)).toHaveAttribute("aria-hidden", "true");
    expect(theSwitch(THEFT)).toHaveAccessibleName(THEFT);
    expect([theSwitch(THEFT).tagName, theSwitch(THEFT).getAttribute("type"), theSwitch(THEFT).getAttribute("role")]).toEqual([
      "INPUT",
      "checkbox",
      "switch",
    ]);
    expect(theSwitch(THEFT).closest("label")).toHaveClass("target");
    expect(theSwitch(THEFT).closest("label")).toHaveTextContent(`${SWITCH.off}${THEFT}`);
  });

  test("test_the_word_follows_the_press_at_once_and_is_drawn_again_from_the_answer", async () => {
    const { open, user, sent, again } = show();
    await open(DIMENSION.crime);

    await user.click(theSwitch(THEFT));
    expect(wordOf(THEFT)).toHaveTextContent(/^On$/);
    expect(sent).toEqual([edits.featureOn("crime_burglary_theft")]);
    // The answer came back and it counts for nothing still: the edit was refused.
    again(first, 2);
    expect(wordOf(THEFT)).toHaveTextContent(/^Off$/);
    expect(theSwitch(THEFT)).not.toBeChecked();

    await user.click(theSwitch(THEFT));
    again(theftOn, 3);
    expect(wordOf(THEFT)).toHaveTextContent(/^On$/);
    expect(theSwitch(THEFT)).toBeChecked();
  });

  test("test_a_press_on_its_word_on_its_lamp_or_on_the_name_of_the_thing_is_a_press_on_the_switch", async () => {
    const { open, user, sent } = show();
    await open(DIMENSION.crime);

    await user.click(wordOf(THEFT) as Element);
    await user.click(within(rowOf(VIOLENCE)).getByText(VIOLENCE));

    expect(sent).toEqual([edits.featureOn("crime_burglary_theft"), edits.featureOn("crime_violence_robbery")]);
  });

  test("test_by_keyboard_the_switch_is_one_stop_and_space_turns_it", async () => {
    const { open, user, sent } = show();
    await open(DIMENSION.crime);
    theSwitch(THEFT).focus();

    await user.keyboard(" ");

    expect(sent).toEqual([edits.featureOn("crime_burglary_theft")]);
    expect(theSwitch(THEFT)).toHaveFocus();
    expect(wordOf(THEFT)).toHaveTextContent(/^On$/);
  });
});

describe("a switch, as it is drawn", () => {
  test("test_what_is_on_is_amber_with_its_lamp_lit_as_what_is_chosen_is_everywhere_in_the_look", async () => {
    const { open } = show();
    await open(DIMENSION.crime);
    const lever = theSwitch(THEFT).parentElement as HTMLElement;

    // The picture of a button of the look, and of the button that is on: the very ones a choice is drawn by.
    expect(lever).toHaveClass("lever");
    expect(["--art", "--art-down", "--art-on", "--art-on-down"].map((name) => lever.style.getPropertyValue(name))).toEqual(
      ["ui-button", "ui-button-down", "ui-button-on", "ui-button-on-down"].map(served),
    );
    expect(["--cut-top", "--cut-right", "--cut-foot", "--cut-left"].map((name) => lever.style.getPropertyValue(name))).toEqual(
      (cutOf("ui-button") ?? []).map(String),
    );
    expect(wordOf(THEFT)).toHaveClass("face");
    const [on, chosen] = [setsOf(".lever > input:checked + .face"), setsOf(".choice > input:checked + .face")];
    expect([...on]).toEqual([...chosen]);
    expect([on.get("border-image-source"), on.get("background-color"), on.get("color")]).toEqual([
      "var(--art-on)",
      "var(--chosen)",
      "var(--on-chosen)",
    ]);
    // Amber is not told from cream by everyone: its lamp is lit, and it says so in its word.
    expect([...setsOf(".lever > input:checked + .face::before")]).toEqual([...setsOf(".choice > input:checked + .face::before")]);
    expect(setsOf(".lever > input:checked + .face::before").get("background")).toMatch(/^linear-gradient\(var\(--ink\), var\(--ink\)\) center \/ /);
  });

  test("test_the_switch_is_laid_over_the_whole_of_its_face_and_is_clear_so_that_the_face_is_what_is_seen", () => {
    const over = setsOf(".lever > input");

    expect([over.get("position"), over.get("inset"), over.get("width"), over.get("height")]).toEqual(["absolute", "0", "100%", "100%"]);
    expect([over.get("appearance"), over.get("background")]).toEqual(["none", "transparent"]);
    expect(setsOf(".lever").get("position")).toBe("relative");
    // It is a main control: no smaller than one, however short its word.
    expect(setsOf(".lever").get("min-block-size")).toBe("var(--target)");
  });

  test("test_its_word_has_the_room_of_the_longer_of_the_two_so_that_the_switch_is_of_one_size_on_or_off", () => {
    // "Off" is the longer by a letter. Were the face as wide as its word, the name beside
    // the switch went a letter to the left as the switch was turned on.
    const longest = Math.max(SWITCH.on.length, SWITCH.off.length);

    expect(longest).toBe(3);
    expect(setsOf(".says").get("min-inline-size")).toBe(`${longest}ch`);
    // And the switch is as wide as its face, whatever room the name beside it is given.
    expect(setsOf(".lever").get("flex")).toBe("none");
  });

  test("test_under_a_press_its_picture_changes_and_nothing_of_it_moves_or_changes_size", () => {
    const states = STYLES.filter((rule) => /\.lever\b/.test(rule.selector) && /:(hover|focus|focus-visible|focus-within|active)\b/.test(rule.selector));

    expect(states.map((rule) => [rule.selector, [...rule.sets.keys()]])).toEqual([
      [".lever > input:active + .face", ["border-image-source"]],
      [".lever > input:checked:active + .face", ["border-image-source"]],
    ]);
  });

  test("test_with_forced_colours_the_system_draws_its_edge_and_says_which_it_is_by_its_own_colour", () => {
    const forced = ALL.filter((rule) => /forced-colors/.test(rule.under ?? "") && /\.lever\b/.test(rule.selector));

    expect(forced.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      [".lever > input:checked + .face", [["border-image-source", "none"], ["border-color", "Highlight"]]],
      [".lever > input:active + .face", [["border-image-source", "none"]]],
      [".lever > input:checked:active + .face", [["border-image-source", "none"]]],
    ]);
  });
});

describe("what a switch shows has its room while the switch is off", () => {
  test("test_a_thing_that_is_off_offers_no_slider_and_the_room_of_its_slider_is_kept_by_its_drawing_at_rest", async () => {
    // The founder: "there is toomuch layout shift when toggling".
    const { open } = show();
    await open(DIMENSION.crime);
    const room = roomOf(THEFT);

    expect(within(rowOf(THEFT)).queryByRole("slider")).toBeNull();
    expect(within(rowOf(THEFT)).queryByRole("textbox")).toBeNull();
    expect(within(rowOf(THEFT)).getAllByRole("switch")).toHaveLength(1);
    // Its room is there, and in it the slider at rest: a drawing, which says nothing to
    // whoever hears the page, and nothing of which takes a press, a key or the focus.
    const rests = room.querySelector("[data-rests]") as HTMLElement;
    expect(rests).toHaveClass("slider");
    expect(rests).toHaveAttribute("aria-hidden", "true");
    expect(rests).toHaveTextContent(FEATURES.howMuch);
    expect(taking(room)).toEqual([]);
    expect(taking(rowOf(THEFT))).toEqual([theSwitch(THEFT)]);
  });

  test("test_turned_on_its_slider_stands_in_the_room_its_drawing_kept_and_is_made_as_the_drawing_was", async () => {
    const { open, again } = show();
    await open(DIMENSION.crime);
    const off = madeAs(roomOf(THEFT));
    // A slider is its name, and a row of a minus, a gauge, a plus and a figure.
    expect(off.filter((line) => !line.startsWith("    "))).toEqual([
      "div.slider",
      "  span.label",
      "  div.row",
    ]);

    again(theftOn, 2);

    expect(within(rowOf(THEFT)).getByRole("slider", { name: FEATURES.weight(THEFT) })).toHaveValue("50");
    const on = madeAs(roomOf(THEFT));
    // Made of the same parts in the same order, each of the class that lays it out: what
    // differs is that a part of the drawing is a control of the slider.
    const plain = (lines: readonly string[]) => lines.map((line) => line.replace(/\b(label|span|button|input|output|p)\./, "."));
    const parts = (lines: readonly string[]) => plain(lines).filter((line) => !/\.(range|cell|mark|drawn|name)$/.test(line.trim()));
    expect(parts(on)).toEqual(parts(off));
    expect(roomOf(THEFT).querySelector("[data-rests]")).toBeNull();
  });

  test("test_the_room_of_every_thing_of_a_group_is_made_alike_whether_the_thing_is_on_or_off", async () => {
    const { open } = show(theftOn);
    await open(DIMENSION.crime);
    const crime = meta.features.filter((metric) => metric.dimension === "crime");
    const rooms = crime.map((metric) => rowOf(metric.short_label));

    // One of them is on, and the rest are off.
    expect(crime.map((metric) => theSwitch(metric.short_label)).filter((one) => (one as HTMLInputElement).checked)).toHaveLength(1);
    for (const room of rooms) {
      expect([...room.children].map((one) => one.classList[0])).toEqual(["check", "inner"]);
      expect([...(room.querySelector(".inner") as HTMLElement).children].map((one) => one.classList[0])).toEqual(["slider"]);
    }
  });

  test("test_where_either_way_can_count_the_room_of_the_two_ways_is_kept_as_well", async () => {
    const { open } = show(nights);
    await open(GOING_OUT, FEATURES.madeOfName("Going out"), STREETS);
    const either = meta.features.filter((metric) => metric.rankable && metric.polarity === "either");
    const [on, off] = ["Pubs and bars", "What homes sell for"];

    expect(either.map((metric) => metric.short_label)).toEqual(expect.arrayContaining([on, off]));
    expect(theSwitch(on)).toBeChecked();
    expect(theSwitch(off)).not.toBeChecked();
    for (const name of [on, off]) {
      expect([name, [...roomOf(name).children].map((one) => `${one.tagName.toLowerCase()}.${one.classList[0]}`)]).toEqual([
        name,
        ["div.slider", "fieldset.radios"],
      ]);
      const ways = roomOf(name).querySelector("fieldset") as HTMLElement;
      expect([name, [...ways.querySelectorAll(".face")].map((face) => face.textContent)]).toEqual([name, [DIRECTION.more, DIRECTION.less]]);
      expect([name, ways.querySelector("legend")?.textContent]).toEqual([name, FEATURES.whichWay]);
    }
    // On, a way can be chosen, and one is. Off, the two are drawn at rest: neither is
    // chosen, for nothing was, and nothing of them takes a press or is heard.
    expect(within(rowOf(on)).getByRole("radio", { name: DIRECTION.more })).toBeChecked();
    expect(within(rowOf(off)).queryAllByRole("radio")).toEqual([]);
    const rests = roomOf(off).querySelector("fieldset") as HTMLFieldSetElement;
    expect([rests.disabled, rests.getAttribute("aria-hidden"), rests.hasAttribute("data-rests")]).toEqual([true, "true", true]);
    expect([...rests.querySelectorAll<HTMLInputElement>("input")].map((one) => one.checked)).toEqual([false, false]);
    expect(taking(roomOf(off))).toEqual([]);
  });

  test("test_under_the_name_of_a_thing_its_slider_and_its_two_ways_are_seen_by_the_start_of_their_names", async () => {
    // Each said the name of the thing again under it, on every row, on and off: what is seen
    // of each is the start of its name, and the whole is heard.
    const { open } = show(nights);
    await open(GOING_OUT, FEATURES.madeOfName("Going out"), STREETS);

    expect([FEATURES.weight("A thing"), FEATURES.direction("A thing")]).toEqual([`${FEATURES.howMuch}: A thing`, `${FEATURES.whichWay}: A thing`]);
    for (const name of ["Pubs and bars", "What homes sell for"]) {
      expect([name, roomOf(name).querySelector(".slider .name")?.textContent]).toEqual([name, FEATURES.howMuch]);
      expect([name, roomOf(name).querySelector("legend")?.textContent]).toEqual([name, FEATURES.whichWay]);
    }
    // Whoever hears the page hears the whole of each, of the thing that is on, word for word.
    expect(within(rowOf("Pubs and bars")).getByRole("slider")).toHaveAccessibleName(FEATURES.weight("Pubs and bars"));
    expect(within(rowOf("Pubs and bars")).getByRole("group", { name: FEATURES.direction("Pubs and bars") })).toHaveAccessibleName(
      FEATURES.direction("Pubs and bars"),
    );
  });

  test("test_what_is_at_rest_is_quieter_in_the_colour_the_look_has_for_that", () => {
    expect(setsOf(".radios[data-rests]").get("color")).toBe("var(--muted)");
    expect(setsOf(".choice > input:disabled + .face").get("color")).toBe("var(--muted)");
    expect(setsOf(".choice > input:disabled + .face").get("border-image-source")).toBe("var(--art-down)");
  });

  test("test_a_thing_that_counts_one_way_keeps_no_room_for_a_choice_it_never_asks", async () => {
    const { open } = show(theftOn);
    await open(DIMENSION.crime, SETTINGS.airAndNoise);

    for (const name of [THEFT, VIOLENCE, "Cleaner air"]) expect(rowOf(name).querySelector("fieldset")).toBeNull();
  });

  test("test_what_the_scale_means_is_said_at_the_head_of_a_group_whether_or_not_a_thing_of_it_is_on", async () => {
    // It was drawn as the first thing of a group was turned on, over all the group holds,
    // and every thing of the group went a line down the page, the one that was pressed among them.
    const { open, again } = show();
    await open(DIMENSION.crime, DIMENSION.brands);
    const crime = document.getElementById(screen.getByRole("button", { name: DIMENSION.crime }).getAttribute("aria-controls") ?? "") as HTMLElement;
    const brands = document.getElementById(screen.getByRole("button", { name: DIMENSION.brands }).getAttribute("aria-controls") ?? "") as HTMLElement;
    const said = (group: HTMLElement) => within(group).queryAllByText(SLIDER.range).filter((line) => line.closest("[aria-hidden='true']") === null);

    expect(within(crime).getAllByRole("switch").filter((one) => (one as HTMLInputElement).checked)).toEqual([]);
    expect(said(crime)).toHaveLength(1);
    expect(said(brands)).toHaveLength(1);
    const was = [...(crime.firstElementChild as HTMLElement).children].map((one) => one.tagName);

    again(theftOn, 2);

    expect(said(crime)).toHaveLength(1);
    expect([...(crime.firstElementChild as HTMLElement).children].map((one) => one.tagName)).toEqual(was);
    expect(within(crime).getByRole("slider")).toHaveAccessibleDescription(SLIDER.range);
  });

  test("test_with_switches_on_and_off_the_settings_have_no_accessibility_fault", async () => {
    const { container, open } = show(nights);
    await open(GOING_OUT, FEATURES.madeOfName("Going out"), STREETS, DIMENSION.crime);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("where the slider of a thing stands, in a box that is wide", () => {
  test("test_it_stands_beside_the_name_of_its_thing_by_one_line_which_may_have_it_under", async () => {
    // The room of a slider is kept while its thing is off, so a group is as long as if
    // every thing of it were on. Beside its name, a row is half as high.
    const { open } = show();
    await open(DIMENSION.crime);

    expect(SLIDER_STANDS_ARE).toEqual(["beside", "under"]);
    expect(SLIDER_STANDS).toBe("beside");
    for (const one of screen.getAllByRole("switch")) {
      expect(one.closest("[role='group']")).toHaveAttribute("data-slider", SLIDER_STANDS);
    }
  });

  test("test_it_is_laid_out_by_the_width_of_the_box_and_in_a_narrow_one_it_stands_under_as_it_did", () => {
    const wide = ALL.filter((rule) => /\.weight\[data-slider="beside"\]/.test(rule.selector));

    expect(wide.length).toBeGreaterThan(0);
    // By the width of what holds the settings, and never by that of the screen: on a phone nothing of it holds.
    expect([...new Set(wide.map((rule) => rule.under))]).toEqual(["@container (min-width: 34rem)"]);
    const set = (selector: string) => new Map(wide.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));
    // Its switch, its name and what is said of it stand at the near side, and its slider at the far side.
    // The far side is given its width: a slider says how wide it is, and so asks for none.
    // Seen in a browser: asked to be as wide as what it held, it was 10 px wide.
    expect(set('.weight[data-slider="beside"]').get("grid-template-columns")).toBe("minmax(0, 1fr) 19rem");
    // A slider, its two buttons and its figure are 280 px, and stand 10 px in from the rule beside them.
    expect(19 * 16).toBeGreaterThanOrEqual(280 + 10);
    // It is the stack of the groups that is asked, which is there wherever the settings are.
    expect(setsOf(".stack").get("container-type")).toBe("inline-size");
    expect(set('.weight[data-slider="beside"] > .inner').get("grid-column")).toBe("2");
    // Why a change was not taken is said under both, from one side of the row to the other.
    expect(set('.weight[data-slider="beside"] > .problem').get("grid-column")).toBe("1 / -1");
    // The two ways stand one under the other there, so that the far side is as wide as a slider.
    expect(set('.weight[data-slider="beside"] .options').get("flex-direction")).toBe("column");
  });

  test("test_the_order_in_which_a_row_is_read_and_reached_is_as_it_was", async () => {
    const { open } = show(nights);
    await open(GOING_OUT, FEATURES.madeOfName("Going out"));
    const row = rowOf("Pubs and bars");
    const read = [...row.querySelectorAll("input, button")].map((one) => one.getAttribute("role") ?? one.getAttribute("type") ?? one.tagName.toLowerCase());

    // The switch, then its slider, then its two ways: nothing is put in another order to be laid out.
    expect(read).toEqual(["switch", "button", "range", "button", "text", "radio", "radio"]);
    expect(STYLES.filter((rule) => rule.sets.has("order")).map((rule) => rule.selector)).toEqual([]);
  });
});
