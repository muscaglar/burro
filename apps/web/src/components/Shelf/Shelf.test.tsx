import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";

import { CRIME_ACCOUNT, CRIME_RULE } from "@/content/crime";
import { READING, READING_TOWARDS } from "@/content/labels";
import { LEGEND } from "@/content/map";
import { SHELF, STRIP } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations, Tag, TagId } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";
import { HEAD, type Opens } from "@/lib/sight";
import { readingOf } from "@/lib/vibes";

import { faultsIn } from "../../../test/support/axe";
import { problemsWith } from "../../../test/support/contract";
import { isFor, rulesOf } from "../../../test/support/css";
import { figuresNotFrom } from "../../../test/support/figures";
import { ROUGH, sayingSo } from "../../../test/support/rough";
import { watch } from "../../../test/support/watch";
import { Helpers } from "../Helpers/Helpers";
import { laidOut, type Sizes } from "../Helpers/laid";
import { drawingOf as chosenFor } from "../kit/Thing/drawn";
import { inShelfOrder, ON_THE_SHELF, Shelf, wordOf } from "./Shelf";

const meta = recordedAnswer("get_meta", "meta").body.data;
const other = recordedAnswer("get_meta", "variant-a/meta").body.data;
const tagOf = (tagId: string, from = meta) => from.tags.find((tag) => tag.tag_id === tagId) as Tag;

const geometry = recordedAnswer("get_geometry", "geometry").body.data;
const { bands } = recordedAnswer("list_areas", "areas").body.data;

interface Shown {
  readonly told: { added: Operations[]; opened: (TagId | null)[] };
  readonly form?: typeof meta;
  /** False to draw the shelf as it is before the boundaries of the areas have come. */
  readonly withTheCity?: boolean;
  /** True to hand it what the release holds of each recipe, so that a word no area is placed on stands apart. */
  readonly withRecipes?: boolean;
  /** Where the card of a word stands. Left out, as the look has chosen. */
  readonly opens?: Opens;
}

/** The shelf, held as the page holds it: the page says which card is open. */
function Held({ told, form = meta, withTheCity = true, withRecipes = false, opens }: Shown) {
  const [open, setOpen] = useState<TagId | null>(null);
  return (
    <Shelf
      tags={form.tags}
      features={form.features}
      recipes={withRecipes ? form.recipes : undefined}
      open={open}
      opens={opens}
      onOpen={(tagId) => {
        told.opened.push(tagId);
        setOpen(tagId);
      }}
      onAdd={(operations) => told.added.push(operations)}
      geometry={withTheCity ? geometry : null}
      bands={bands}
    />
  );
}

function show(form = meta, withTheCity = true, opens?: Opens) {
  const told = { added: [] as Operations[], opened: [] as (TagId | null)[] };
  const view = render(<Held told={told} form={form} withTheCity={withTheCity} opens={opens} />);
  return { ...told, user: userEvent.setup({ delay: null }), ...view };
}

const shelf = () => within(screen.getByRole("region", { name: SHELF.title }));
const word = (name: string) => shelf().getByRole("button", { name });
const card = (name: string) => within(screen.getByRole("region", { name }));
/** A fold of a card, by what its bar says: the browser's own element, which holds what is long. */
const foldOf = (name: string, says: string) => {
  const folds = [...screen.getByRole("region", { name }).querySelectorAll("details")];
  const found = folds.find((fold) => fold.querySelector("summary")?.textContent?.startsWith(says));
  if (found === undefined) throw new Error(`no fold of the card says ${says}`);
  return found;
};

describe("the shelf, under the helper that opens it", () => {
  /** The shelf as the first screen holds it: under a helper, which the page names. */
  function under(label: string) {
    const told = { added: [] as Operations[], opened: [] as (TagId | null)[] };
    const view = render(
      <Helpers
        label="Other ways to start"
        helpers={[{ id: "word", label, children: <Held told={told} /> }]}
        open="word"
        onOpen={() => undefined}
      />,
    );
    return { ...told, user: userEvent.setup({ delay: null }), ...view };
  }

  test("test_under_the_helper_of_its_name_it_draws_no_heading_and_is_named_by_the_helper", () => {
    // Seen in a browser: "Start from a word" stood directly under "Start from a word".
    under(SHELF.title);
    const helper = screen.getByRole("button", { name: SHELF.title });
    const region = screen.getByRole("region", { name: SHELF.title });

    expect(screen.queryByRole("heading", { name: SHELF.title })).toBeNull();
    expect(region.querySelector("h2")).toBeNull();
    // It is the region it was, by the name it had: the helper over it says the name.
    expect(region).toHaveAttribute("aria-labelledby", helper.id);
    expect(region.textContent?.startsWith(SHELF.title)).toBe(false);
    expect(shelf().getAllByRole("button").length).toBeGreaterThan(ON_THE_SHELF);
  });

  test("test_under_a_helper_of_another_name_its_heading_is_kept_for_a_screen_reader_and_not_drawn", () => {
    under("Another way in");
    const region = screen.getByRole("region", { name: SHELF.title });
    const heading = within(region).getByRole("heading", { level: 2, name: SHELF.title });

    expect(heading).toHaveClass("visually-hidden");
    expect(region).toHaveAttribute("aria-labelledby", heading.id);
  });

  test("test_the_shelf_says_what_a_word_of_it_is_and_what_a_press_does_before_any_is_pressed", () => {
    // Seen as a stranger would see it: a box of words with a drawing beside each, and
    // nothing to say what they were or what a press on one would do.
    under(SHELF.title);
    const region = screen.getByRole("region", { name: SHELF.title });
    const lead = within(region).getByText(SHELF.lead);

    expect(lead.tagName).toBe("P");
    // It comes before the words it speaks of, and says what a vibe is in words of every day.
    const first = shelf().getAllByRole("button")[0] as HTMLElement;
    expect(lead.compareDocumentPosition(first) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(SHELF.lead).toMatch(/a vibe, which is a way of describing what an area feels like/);
    // It names no vibe: the words of the shelf are the release's.
    for (const tag of meta.tags) {
      expect([tag.label, new RegExp(`\\b${wordOf(tag)}\\b`, "i").test(SHELF.lead)]).toEqual([tag.label, false]);
    }
  });

  test("test_alone_it_stands_under_its_own_heading_as_it_did", () => {
    show();
    const heading = shelf().getByRole("heading", { level: 2, name: SHELF.title });

    expect(heading).not.toHaveClass("visually-hidden");
    expect(heading).toHaveClass("title");
  });

  test("test_where_it_has_no_heading_what_is_headed_in_it_is_headed_one_level_up_so_that_none_is_skipped", async () => {
    // Found by the check of the structure of the page: with the heading of the shelf gone the
    // name of a card, which was one level under it, stood two levels under the heading of the page.
    const levels = (part: HTMLElement) =>
      [...part.querySelectorAll<HTMLElement>("h1, h2, h3, h4, [role='heading']")].map((heading) =>
        Number(heading.getAttribute("aria-level") ?? heading.tagName[1]),
      );
    const named = under(SHELF.title);
    await named.user.click(word("leafy"));
    expect(levels(named.container)).toEqual([2, 3, 3]);
    expect(card("Leafy").getByRole("heading", { level: 2, name: "Leafy" })).toBeInTheDocument();
    named.unmount();

    const alone = show();
    await alone.user.click(word("leafy"));
    expect(levels(alone.container)).toEqual([2, 3, 4, 4]);
    expect(card("Leafy").getByRole("heading", { level: 3, name: "Leafy" })).toBeInTheDocument();
  });

  test("test_the_words_that_cannot_be_added_stand_under_a_small_heading_at_whichever_level", async () => {
    const preview = recordedAnswer("get_meta", "preview/meta").body.data;
    const told = { added: [] as Operations[], opened: [] as (TagId | null)[] };
    const view = render(
      <Helpers
        label="Other ways to start"
        helpers={[{ id: "word", label: SHELF.title, children: <Held told={told} form={preview} withRecipes /> }]}
        open="word"
        onOpen={() => undefined}
      />,
    );
    const more = screen.queryByRole("button", { name: SHELF.more });
    if (more !== null) await userEvent.setup({ delay: null }).click(more);

    const waiting = screen.getByRole("heading", { name: SHELF.waiting });
    expect(waiting).toHaveAttribute("aria-level", "2");
    expect(waiting.tagName).toBe("P");
    expect(await faultsIn(view.container)).toEqual([]);
  });

  test("test_the_card_of_a_word_opens_as_it_did_and_the_shelf_has_no_fault_under_its_helper", async () => {
    const { user, container } = under(SHELF.title);

    await user.click(word("leafy"));

    expect(card("Leafy").getByRole("button", { name: SHELF.add })).toBeInTheDocument();
    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the shelf a search can start from", () => {
  test("test_seven_words_stand_on_the_shelf_in_the_order_the_api_gives_and_the_rest_are_under_more", async () => {
    const { user } = show();
    const words = () =>
      shelf()
        .getAllByRole("button")
        .map((button) => button.textContent);

    expect(ON_THE_SHELF).toBe(7);
    expect(words()).toEqual(["leafy", "villagey", "lively", "quiet street", "period", "walkable", "near a big park", SHELF.more]);
    expect(words().slice(0, 7)).toEqual(inShelfOrder(meta.tags).slice(0, 7).map(wordOf));

    await user.click(word(SHELF.more));

    expect(words()).toEqual([...inShelfOrder(meta.tags).map(wordOf), SHELF.fewer]);
    expect(words()).toHaveLength(meta.tags.length + 1);
    // The button stays where it was, and keeps the focus.
    expect(word(SHELF.fewer)).toHaveFocus();
    expect(word(SHELF.fewer)).toHaveAttribute("aria-expanded", "true");
  });

  test("test_a_vibe_with_no_everyday_word_stands_under_its_own_name", async () => {
    const { user } = show();
    await user.click(word(SHELF.more));

    const unworded = meta.tags.filter((tag) => tag.shelf_word === null);
    expect(unworded.map((tag) => tag.tag_id).sort()).toEqual([
      "family_amenities",
      "family_area",
      "foodie",
      "homes",
      "street_character",
      "well_connected",
      "young_professionals",
    ]);
    for (const tag of unworded) expect(word(tag.short_label)).toBeInTheDocument();
  });

  test("test_a_word_opens_the_card_of_its_vibe_and_sends_nothing", async () => {
    const watching = watch();
    try {
      const { user, added, opened } = show();

      await user.click(word("lively"));

      expect(word("lively")).toHaveAttribute("aria-expanded", "true");
      expect(opened).toEqual(["pace"]);
      expect(added).toEqual([]);
      // Which word was pressed is told to nobody: nothing is fetched, stored or written down.
      expect(watching.console).toEqual([]);
      expect(watching.storage).toEqual([]);
      expect(watching.history).toEqual([]);
    } finally {
      watching.stop();
    }
  });

  test("test_the_card_says_what_the_vibe_means_what_it_is_made_of_and_what_it_cannot_see", async () => {
    const { user } = show();
    const pace = tagOf("pace");

    await user.click(word("lively"));
    const opened = card("Going out");

    expect(opened.getByText(pace.meaning)).toBeInTheDocument();
    expect(opened.getByText(SHELF.scale("Calm", "Buzzy"))).toBeInTheDocument();
    const recipe = foldOf("Going out", SHELF.recipe);
    expect([...recipe.querySelectorAll("li")].map((part) => part.textContent)).toEqual(
      pace.terms.map((term) => {
        const metric = meta.features.find((one) => one.feature_id === term.feature_id);
        return `${SHELF.share(term.hundredths)} ${metric?.label}${readingOf(pace, term.reading)}`;
      }),
    );
    expect(pace.terms.reduce((sum, term) => sum + term.hundredths, 0)).toBe(100);
    const cannot = foldOf("Going out", SHELF.cannotSee);
    expect([...cannot.querySelectorAll("li")].map((line) => line.textContent)).toEqual(pace.cannot_see);
    expect(pace.cannot_see.length).toBeGreaterThan(1);
  });

  test("test_a_part_of_a_scale_says_which_end_a_higher_figure_counts_towards", async () => {
    // Seen in a browser, of flats as a share of homes: "A higher figure means more of this
    // vibe", in a card that says the vibe runs from Houses to Flats. Neither end of a scale
    // is more of it, and the page of vibes and the page of an area name the end.
    const { user } = show();
    const said = (name: string) =>
      [...foldOf(name, SHELF.recipe).querySelectorAll("li")].map((part) => part.lastElementChild?.textContent);
    const homes = tagOf("homes");
    // A part is drawn where the release names what it measures.
    const drawn = homes.terms.filter((term) => meta.features.some((one) => one.feature_id === term.feature_id));

    await user.click(word(SHELF.more));
    await user.click(word(homes.short_label));
    expect(homes.high_end).toBe("Flats");
    expect(said(homes.label)).toEqual(drawn.map((term) => READING_TOWARDS[term.reading]("Flats")));
    expect(said(homes.label)).toContain("A higher figure counts towards Flats");
    // A vibe that runs one way has no end to name, and says what it said.
    await user.click(word("leafy"));
    expect(tagOf("leafy").high_end).toBeNull();
    expect(said("Leafy")).toEqual(tagOf("leafy").terms.map((term) => READING[term.reading]));
  });

  test("test_what_is_long_in_a_card_is_folded_in_the_browsers_own_element_and_is_one_press_away", async () => {
    // Measured on a phone: the card of a word was 1,170 px high, of which what the vibe is
    // made of and what it cannot see were 600. It had room neither under its word nor over
    // it, and the word went 184 px from under the hand as its head was brought into sight.
    const { user } = show();
    await user.click(word("leafy"));

    const folds = [foldOf("Leafy", SHELF.recipe), foldOf("Leafy", SHELF.cannotSee)];
    expect(folds.map((fold) => [fold.tagName, fold.open])).toEqual([
      ["DETAILS", false],
      ["DETAILS", false],
    ]);
    // Each says what it holds, and of which vibe to whoever hears the page.
    expect(folds.map((fold) => fold.querySelector("summary")?.textContent)).toEqual([
      `${SHELF.recipe}: Leafy`,
      `${SHELF.cannotSee}: Leafy`,
    ]);
    // What it holds is in the page while it is closed, and is shown by a press on its bar.
    expect(folds[0]?.querySelectorAll("li")).toHaveLength(tagOf("leafy").terms.length);
    await user.click(folds[0]?.querySelector("summary") as HTMLElement);
    expect(folds[0]?.open).toBe(true);
    // A card that is opened after it begins closed.
    await user.click(word("lively"));
    expect(foldOf("Going out", SHELF.recipe).open).toBe(false);
  });

  test("test_the_card_of_a_word_holds_the_city_coloured_by_it_in_five_bands_with_its_legend", async () => {
    // Seen on a phone: a word was pressed and its card opened. The map it coloured was two
    // screens down, at 1,713 px, and its legend had no height until another button was pressed.
    const { user } = show();
    await user.click(word("lively"));
    const opened = card("Going out");
    const marks = bands.find((one) => one.tag_id === "pace")?.marks ?? [];

    const picture = opened.getByRole("img", { name: LEGEND.vibe("Going out") });
    const drawn = [...picture.querySelectorAll("path[data-area]")];
    expect(drawn).toHaveLength(geometry.features.length);
    for (const mark of marks) {
      const area = drawn.find((one) => one.getAttribute("data-area") === mark.area_id);
      expect(area?.getAttribute("data-band")).toBe(mark.band === null ? "none" : String(mark.band));
    }
    // The legend names the five bands, and both ends of the vibe by the names the API gives them.
    const legend = within(opened.getByRole("list", { name: LEGEND.title }));
    expect(legend.getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      LEGEND.vibeEnd(1, "Calm"),
      LEGEND.vibeBand(2),
      LEGEND.vibeBand(3),
      LEGEND.vibeBand(4),
      LEGEND.vibeEnd(5, "Buzzy"),
      ...(marks.some((mark) => mark.band === null) ? [LEGEND.notPlaced] : []),
    ]);
  });

  test("test_the_city_in_the_card_is_for_a_narrow_screen_where_the_map_is_out_of_sight", () => {
    // On a wide screen the map is beside the shelf, and is coloured by the word that is open.
    const rules = rulesOf(readFileSync(path.join(__dirname, "Shelf.module.css"), "utf8"));
    const city = rules.filter((rule) => isFor(rule.selector, "city"));

    expect(city.filter((rule) => rule.sets.get("display") === "none").map((rule) => rule.under)).toEqual([
      "@media (min-width: 60rem)",
    ]);
  });

  test("test_before_the_boundaries_of_the_areas_have_come_the_card_holds_no_picture", async () => {
    const { user } = show(meta, false);
    await user.click(word("leafy"));

    expect(card("Leafy").queryByRole("img")).toBeNull();
    expect(card("Leafy").queryByRole("list", { name: LEGEND.title })).toBeNull();
    expect(card("Leafy").getByRole("button", { name: SHELF.add })).toBeInTheDocument();
  });

  test("test_the_button_that_adds_the_word_stands_before_what_the_vibe_is_made_of", async () => {
    // Seen in a browser: "Add to my search" was at 1,114 px on a phone, below the first screen,
    // and on a desk only its top edge showed.
    const { user } = show();
    await user.click(word("leafy"));
    const opened = card("Leafy");
    const before = (one: Element, other: Element) => Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);

    const add = opened.getByRole("button", { name: SHELF.add });
    expect(before(opened.getByText(tagOf("leafy").meaning), add)).toBe(true);
    expect(before(add, opened.getByRole("img", { name: LEGEND.vibe("Leafy") }))).toBe(true);
    expect(before(add, foldOf("Leafy", SHELF.recipe))).toBe(true);
    expect(before(add, foldOf("Leafy", SHELF.cannotSee))).toBe(true);
  });

  describe("where the card of a word stands", () => {
    // Measured at 1440 by 900: a word was pressed at 797, and went to 608 as the head of its
    // card was brought into sight, 189 px from under the hand. On a phone it went 184 px.
    /** What holds every word of the shelf, and nothing of a card. It is no part that is named: the shelf is. */
    const words = () => document.querySelector("[data-words]") as HTMLElement;
    const place = () => document.querySelector('[id$="-card"]');
    const browser = (sizes: Sizes) => laidOut(sizes, { line: words, opened: place });
    /** A desk, with the words at the foot of the window, and the card of a word as high as it was measured. */
    const A_DESK: Sizes = { window: 900, line: 760, lineHigh: 120, opens: 615 };

    test("test_the_words_of_the_shelf_are_one_part_which_the_card_stands_under_or_over", async () => {
      const { user } = show();

      expect(words()).toContainElement(word("leafy"));
      expect(words()).toContainElement(word(SHELF.more));
      expect(words().contains(place())).toBe(false);
      await user.click(word("leafy"));
      expect(words().contains(place())).toBe(false);
    });

    test("test_what_a_hand_opens_stands_over_the_words_where_it_has_no_room_under_them_and_the_word_stays_where_it_was_pressed", async () => {
      const { user } = show();
      const laid = browser(A_DESK);
      try {
        expect(laid.stands(word("leafy"))).toEqual([760, 880]);

        await user.click(word("leafy"));

        expect(card("Leafy").getByRole("button", { name: SHELF.add })).toBeInTheDocument();
        expect(laid.over()).toBe(true);
        // The page went on by as much as was put over the words, and the word is where it was.
        expect(laid.asked).toEqual([615 + 12]);
        expect(laid.stands(word("leafy"))).toEqual([760, 880]);
        // The card is whole and in sight, over the words.
        expect(laid.stands(place())).toEqual([760 - 12 - 615, 760 - 12]);
        expect(word("leafy")).toHaveFocus();
      } finally {
        laid.putBack();
      }
    });

    test("test_where_the_card_has_room_under_the_words_it_stands_there_and_nothing_is_moved", async () => {
      const { user } = show();
      const laid = browser({ ...A_DESK, line: 100 });
      try {
        await user.click(word("leafy"));

        expect(laid.over()).toBe(false);
        expect(laid.asked).toEqual([]);
        expect(laid.stands(word("leafy"))).toEqual([100, 220]);
      } finally {
        laid.putBack();
      }
    });

    test("test_a_card_that_has_room_neither_way_stands_under_the_words_and_its_head_is_brought_into_sight_by_the_least", async () => {
      // On a phone 844 px high the card of a word is 1,170 px high.
      const { user } = show();
      const laid = browser({ window: 844, line: 640, lineHigh: 200, opens: 1170 });
      try {
        await user.click(word("lively"));

        expect(laid.over()).toBe(false);
        expect(laid.asked).toEqual([640 + 200 + 12 + HEAD - 844]);
        expect(laid.stands(word("lively"))[0]).toBe(640 - 56);
      } finally {
        laid.putBack();
      }
    });

    test("test_another_word_that_is_pressed_stays_where_it_was_pressed_as_its_card_takes_the_place_of_the_first", async () => {
      const { user } = show();
      const laid = browser(A_DESK);
      try {
        await user.click(word("leafy"));

        await user.click(word("lively"));

        expect(card("Going out").getByRole("button", { name: SHELF.close })).toBeInTheDocument();
        expect(laid.over()).toBe(true);
        expect(laid.stands(word("lively"))).toEqual([760, 880]);
      } finally {
        laid.putBack();
      }
    });

    test("test_closed_by_its_word_by_its_own_button_or_by_escape_the_card_goes_and_the_words_stay_where_they_stood", async () => {
      const { user } = show();
      const laid = browser(A_DESK);
      try {
        await user.click(word("leafy"));
        await user.click(word("leafy"));
        expect(screen.queryByRole("region", { name: "Leafy" })).toBeNull();
        expect(laid.stands(word("leafy"))).toEqual([760, 880]);

        await user.click(word("leafy"));
        await user.click(card("Leafy").getByRole("button", { name: SHELF.close }));
        expect(screen.queryByRole("region", { name: "Leafy" })).toBeNull();
        expect(laid.stands(word("leafy"))).toEqual([760, 880]);
        expect(word("leafy")).toHaveFocus();

        await user.click(word("leafy"));
        await user.keyboard("{Escape}");
        expect(screen.queryByRole("region", { name: "Leafy" })).toBeNull();
        expect(laid.stands(word("leafy"))).toEqual([760, 880]);
      } finally {
        laid.putBack();
      }
    });

    test("test_what_the_keys_open_stands_under_the_words_and_the_whole_of_it_is_brought_into_sight_as_far_as_the_word_allows", async () => {
      const { user } = show();
      const laid = browser({ ...A_DESK, line: 600, opens: 300 });
      try {
        word("leafy").focus();
        await user.keyboard("{Enter}");

        expect(card("Leafy").getByRole("button", { name: SHELF.add })).toBeInTheDocument();
        // It has room over the words, and stands under them: nobody's hand is on the word.
        expect(laid.over()).toBe(false);
        // Until its foot is in sight, with a little room under it.
        expect(laid.asked).toEqual([600 + 120 + 12 + 300 + 8 - 900]);
        expect(word("leafy")).toHaveFocus();
      } finally {
        laid.putBack();
      }
    });

    test("test_a_card_that_the_page_opens_of_itself_stands_under_the_words_and_nothing_is_moved", () => {
      render(
        <Shelf tags={meta.tags} features={meta.features} open="leafy" onOpen={() => undefined} onAdd={() => undefined} />,
      );
      const laid = browser(A_DESK);
      try {
        expect(laid.over()).toBe(false);
        expect(laid.asked).toEqual([]);
      } finally {
        laid.putBack();
      }
    });

    test("test_with_its_card_over_the_words_the_shelf_has_no_accessibility_fault", async () => {
      const { user, container } = show();
      const laid = browser(A_DESK);
      try {
        await user.click(word("leafy"));
        expect(laid.over()).toBe(true);
      } finally {
        laid.putBack();
      }
      expect(await faultsIn(container)).toEqual([]);
    });
  });

  test("test_the_other_way_it_was_built_on_a_narrow_screen_a_card_that_opens_under_the_foot_of_the_window_is_brought_up_by_its_head", async () => {
    // Seen on a phone 844 px high: a word was pressed at 653, and its card was brought to
    // the top of the window. The word that was pressed stood 148 px over the top, out of
    // sight, with the focus on it, and the card under it bore another name: "lively" opens
    // "Going out". So the card is brought up as it is on a wide screen: by its head, which
    // leaves the word that was pressed in sight over it, 64 px from where it was pressed.
    const asked: number[] = [];
    const brought: unknown[] = [];
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 844 });
    Element.prototype.scrollIntoView = function scrollIntoView(how?: boolean | ScrollIntoViewOptions) {
      brought.push(how);
    };
    window.matchMedia = ((query: string) => ({ matches: /max-width/.test(query), media: query })) as never;
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const [top, foot] = this.tagName === "BUTTON" ? [653, 697] : this.id.endsWith("-card") ? [860, 2203] : [0, 0];
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((_: number, y: number) => {
      asked.push(y);
    }) as typeof window.scrollBy);
    try {
      const { user } = show(meta, true, "under");

      await user.click(word("lively"));

      expect(card("Going out").getByRole("button", { name: SHELF.add })).toBeInTheDocument();
      expect(asked).toEqual([860 + HEAD - 844]);
      expect(653 - (860 + HEAD - 844)).toBeGreaterThan(0);
      // The card is not brought to the top of the window, over which its word would stand.
      expect(brought).toEqual([]);
      expect(word("lively")).toHaveFocus();

      // Nothing is moved as the card is closed by its word.
      await user.click(word("lively"));
      expect(asked).toHaveLength(1);
    } finally {
      measure.mockRestore();
      scroll.mockRestore();
      Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
      delete (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView;
      delete (window as { matchMedia?: unknown }).matchMedia;
    }
  });

  test("test_the_other_way_it_was_built_on_a_wide_screen_a_card_that_opens_under_the_foot_of_the_window_is_brought_into_sight", async () => {
    // Seen at 1440 by 900: the shelf stands behind a helper, and once it is opened it stands
    // at the foot of the window. A word was pressed at 618, and its card opened from 862:
    // the word turned amber, the map beside it was coloured, and of the card, which holds
    // what the word means and the way to add it, the top edge was in sight.
    const asked: number[] = [];
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
    window.matchMedia = ((query: string) => ({ matches: false, media: query })) as never;
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const [top, foot] = this.tagName === "BUTTON" ? [618, 684] : this.id.endsWith("-card") ? [862, 1570] : [0, 0];
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((_: number, y: number) => {
      asked.push(y);
    }) as typeof window.scrollBy);
    try {
      const { user } = show(meta, true, "under");

      await user.click(word("leafy"));

      expect(card("Leafy").getByRole("button", { name: SHELF.add })).toBeInTheDocument();
      // As far as shows the head of the card, and no further. Seen at 1440 by 900, while the
      // card was brought up until its word stood at the top: the word went 563 px from under
      // the pointer.
      expect(asked).toEqual([862 + HEAD - 900]);
      expect(word("leafy")).toHaveFocus();

      // Nothing is moved as the card is closed by its word.
      await user.click(word("leafy"));
      expect(asked).toHaveLength(1);
    } finally {
      measure.mockRestore();
      scroll.mockRestore();
      Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
      delete (window as { matchMedia?: unknown }).matchMedia;
    }
  });

  test("test_every_word_of_a_card_about_a_vibe_is_the_apis", async () => {
    const { user, container } = show();
    await user.click(word(SHELF.more));

    for (const tag of inShelfOrder(meta.tags)) {
      await user.click(word(wordOf(tag)));
      const opened = screen.getByRole("region", { name: tag.label });
      // Every figure on the card is a share of the recipe, or is in a name the API gives.
      const allowed = new Set([
        // The five bands of the legend, which are counted and are no figure of a place.
        ...[1, 2, 3, 4, 5].flatMap((band) => [LEGEND.vibeBand(band), LEGEND.vibeEnd(band, tag.low_end ?? STRIP.least), LEGEND.vibeEnd(band, tag.high_end ?? STRIP.most)]),
        ...tag.terms.map((term) => SHELF.share(term.hundredths)),
        ...meta.features.map((metric) => metric.label),
        ...tag.cannot_see,
        tag.meaning,
        ...[1, 2, 3, 4, 5].map((count) => SHELF.missing(count)),
      ]);
      expect(figuresNotFrom(opened, allowed)).toEqual([]);
      // No code is shown in place of a name: not the vibe's, and not a part's.
      expect(/[a-z]_[a-z]/.test(opened.textContent ?? "")).toBe(false);
    }
    expect(container.textContent?.includes("undefined")).toBe(false);
  });

  test("test_a_part_the_release_does_not_carry_is_counted_and_never_shown_by_its_code", async () => {
    const { user } = show();
    const onFoot = tagOf("everyday_on_foot");
    const carried = new Set(meta.features.map((metric) => metric.feature_id));
    const missing = onFoot.terms.filter((term) => !carried.has(term.feature_id));

    await user.click(word("walkable"));

    expect(missing.length).toBe(2);
    expect(card("Everyday on foot").getByText(SHELF.missing(2))).toBeInTheDocument();
    for (const term of missing) {
      expect(screen.getByRole("region", { name: "Everyday on foot" }).textContent?.includes(term.feature_id)).toBe(false);
    }
  });

  test("test_add_to_my_search_sends_one_edit_towards_the_end_the_word_means", async () => {
    const { user, added } = show();

    await user.click(word("lively"));
    await user.click(card("Going out").getByRole("button", { name: SHELF.add }));
    await user.click(word("leafy"));
    await user.click(card("Leafy").getByRole("button", { name: SHELF.add }));

    expect(tagOf("pace")).toMatchObject({ shelf_word: "lively", shelf_toward: "high" });
    expect(added).toEqual([edits.tagOn("pace", "high"), edits.tagOn("leafy", "high")]);
    // The edit is the one the API was recorded taking from the shelf.
    expect(added[1]).toEqual((recordedAnswer("rank", "rank-shelf").request.body as { operations: Operations }).operations);
    for (const operations of added) expect(problemsWith("Operations", operations)).toEqual([]);
  });

  test("test_a_scale_with_no_word_of_its_own_asks_which_end", async () => {
    const { user, added } = show();
    await user.click(word(SHELF.more));

    await user.click(word("Houses or flats"));
    const opened = card("Houses or flats");

    expect(tagOf("homes")).toMatchObject({ shape: "scale", shelf_toward: null, low_end: "Houses", high_end: "Flats" });
    expect(opened.queryByRole("button", { name: SHELF.add })).toBeNull();
    await user.click(opened.getByRole("button", { name: SHELF.addToward("Houses") }));
    await user.click(opened.getByRole("button", { name: SHELF.addToward("Flats") }));

    expect(added).toEqual([edits.tagOn("homes", "low"), edits.tagOn("homes", "high")]);
  });

  test("test_the_card_of_a_vibe_that_counts_recorded_crime_says_so_before_it_can_be_added", async () => {
    const { user, added } = show();
    await user.click(word(SHELF.more));

    await user.click(word("Gritty"));
    const opened = card("Gritty");

    // It says what it counts, by the names the API gives, and when recorded crime counts.
    const said = opened.getByRole("note", { name: CRIME_ACCOUNT.counts });
    expect(said).toHaveTextContent(
      `${CRIME_ACCOUNT.counts}: Recorded criminal damage and arson; Recorded anti-social behaviour.`,
    );
    expect(said).toHaveTextContent(CRIME_RULE);
    expect(said).toHaveTextContent(CRIME_ACCOUNT.asking);
    // It stands before what can be pressed, so that it is read first.
    const towards = opened.getByRole("button", { name: SHELF.addToward("Gritty") });
    expect(said.compareDocumentPosition(towards) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // To press an end is the person's own choice, and is sent as one.
    await user.click(towards);
    expect(added).toEqual([edits.tagOn("street_character", "high")]);
  });

  test("test_the_card_of_a_vibe_that_holds_no_recorded_crime_says_nothing_of_it", async () => {
    const { user } = show();
    await user.click(word(SHELF.more));

    for (const tag of meta.tags.filter((one) => one.tag_id !== "street_character")) {
      await user.click(word(wordOf(tag)));
      const opened = card(tag.label);
      expect(opened.queryByRole("note", { name: CRIME_ACCOUNT.counts })).toBeNull();
      expect(screen.getByRole("region", { name: tag.label }).textContent?.includes(CRIME_ACCOUNT.counts)).toBe(false);
    }
  });

  test("test_the_word_and_the_card_of_a_vibe_the_service_holds_less_sure_say_nothing_of_how_sure_it_is", async () => {
    // The founder had the label of a rough guide go, and the sentence that said why: no
    // page passes it on. Its word is a word of the shelf as any other, and so is its card.
    // The service says which vibe it is, in a code, and no word more: what one said until it
    // stopped is laid on the release, as a service may say it again.
    const told = sayingSo(meta);
    const { user, added } = show(told);
    expect([tagOf(ROUGH.tag_id).sureness, told.rough_guides]).toEqual(["rough_guide", [ROUGH]]);

    const villagey = word("villagey");
    expect(villagey.textContent).toBe("villagey");
    expect(villagey.nextElementSibling).toBeNull();

    await user.click(villagey);
    const opened = card("Village feel");

    expect(document.querySelectorAll("[data-rough-guide]")).toHaveLength(0);
    expect(document.body.textContent?.includes(ROUGH.label)).toBe(false);
    expect(document.body.textContent?.includes(ROUGH.why)).toBe(false);
    expect(/rough guide|less sure/i.test(document.body.textContent ?? "")).toBe(false);
    // Nothing is added by opening. To press it is the person's own choice, and is sent as
    // one edit of that vibe alone.
    expect(added).toEqual([]);
    await user.click(opened.getByRole("button", { name: SHELF.add }));
    expect(added).toEqual([edits.tagOn("village_feel", "high")]);
  });

  test("test_no_card_of_the_shelf_says_how_sure_its_vibe_is", async () => {
    // Whatever a service says of whichever vibe: here it holds every vibe less sure, and says so of each.
    const every = sayingSo(meta, meta.tags.map((tag) => tag.tag_id));
    const { user } = show(every);
    await user.click(word(SHELF.more));

    expect(every.rough_guides.map((told) => [told.tag_id, told.label, told.why])).toEqual(meta.tags.map((tag) => [tag.tag_id, ROUGH.label, ROUGH.why]));
    for (const tag of every.tags) {
      await user.click(word(wordOf(tag)));
      const card = screen.getByRole("region", { name: tag.label });
      expect([tag.tag_id, tag.sureness, card.querySelector("[data-rough-guide]")]).toEqual([tag.tag_id, "rough_guide", null]);
      expect([tag.tag_id, card.textContent?.includes(ROUGH.label), card.textContent?.includes(ROUGH.why)]).toEqual([tag.tag_id, false, false]);
      expect([tag.tag_id, /rough guide|less sure/i.test(card.textContent ?? "")]).toEqual([tag.tag_id, false]);
    }
  });

  test("test_one_card_is_open_at_a_time_and_the_word_pressed_again_closes_it", async () => {
    const { user, opened } = show();

    await user.click(word("lively"));
    await user.click(word("leafy"));
    expect(screen.queryByRole("region", { name: "Going out" })).toBeNull();
    expect(screen.getByRole("region", { name: "Leafy" })).toBeInTheDocument();
    expect(shelf().getAllByRole("button", { expanded: true })).toEqual([word("leafy")]);

    await user.click(word("leafy"));

    expect(screen.queryByRole("region", { name: "Leafy" })).toBeNull();
    expect(opened).toEqual(["pace", "leafy", null]);
  });

  test("test_closing_a_card_puts_the_focus_back_on_its_word_and_never_leaves_it_on_nothing", async () => {
    const { user } = show();
    await user.click(word("lively"));

    await user.click(card("Going out").getByRole("button", { name: SHELF.close }));

    expect(screen.queryByRole("region", { name: "Going out" })).toBeNull();
    expect(word("lively")).toHaveFocus();
    expect(word("lively")).toHaveAttribute("aria-expanded", "false");
  });

  test("test_escape_closes_the_card_and_puts_the_focus_back_on_its_word", async () => {
    const { user } = show();
    await user.click(word("period"));
    await user.tab();

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("region", { name: "Age of buildings" })).toBeNull();
    expect(word("period")).toHaveFocus();
  });

  test("test_a_card_under_more_is_never_left_open_with_its_word_out_of_sight", async () => {
    const { user, opened } = show();
    const foodie = tagOf("foodie");
    await user.click(word(SHELF.more));
    await user.click(word(wordOf(foodie)));

    await user.click(word(SHELF.fewer));

    // The word goes out of sight, and its card goes with it. The button keeps the focus.
    expect(screen.queryByRole("region", { name: foodie.label })).toBeNull();
    expect(shelf().queryByRole("button", { name: wordOf(foodie) })).toBeNull();
    expect(opened.at(-1)).toBeNull();
    expect(word(SHELF.more)).toHaveFocus();
    // A card of a word that stays is left as it is.
    await user.click(word("leafy"));
    await user.click(word(SHELF.more));
    await user.click(word(SHELF.fewer));
    expect(screen.getByRole("region", { name: "Leafy" })).toBeInTheDocument();
  });

  test("test_where_gritty_is_built_the_other_way_the_shelf_offers_that_vibe", async () => {
    const { user, added } = show(other);
    await user.click(word(SHELF.more));

    expect(other.gritty_variant).toBe("a");
    expect(other.tags.map((tag) => tag.tag_id)).toContain("works_warehouses");
    expect(other.tags.map((tag) => tag.tag_id)).not.toContain("street_character");
    const works = tagOf("works_warehouses", other);
    await user.click(word(wordOf(works)));
    await user.click(card(works.label).getByRole("button", { name: SHELF.add }));

    expect(works.shape).toBe("one_way");
    expect(added).toEqual([edits.tagOn("works_warehouses", "high")]);
  });

  test("test_every_button_of_the_shelf_is_native_and_takes_a_target_size", async () => {
    const { user, container } = show();
    await user.click(word("lively"));

    const buttons = [...container.querySelectorAll("button")];
    expect(buttons.length).toBeGreaterThan(9);
    expect(buttons.filter((button) => !button.classList.contains("target"))).toEqual([]);
    expect(container.querySelectorAll("[role='button'], [onclick], a")).toHaveLength(0);
  });

  test("test_the_shelf_with_a_card_open_has_no_accessibility_fault", async () => {
    const { user, container } = show();
    await user.click(word("lively"));

    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_with_no_vibe_in_the_release_there_is_no_shelf", () => {
    const { container } = render(
      <Shelf tags={[]} features={meta.features} open={null} onOpen={() => undefined} onAdd={() => undefined} />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});

const SHEET = readFileSync(path.join(__dirname, "Shelf.module.css"), "utf8");
const RULES = rulesOf(SHEET);
const setsOf = (selector: string) =>
  new Map(RULES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));
/** The picture a word of the shelf is drawn with, as the page names it. */
const drawingOf = (button: HTMLElement) =>
  /\/art\/([a-z0-9-]+)\.png/.exec(button.querySelector<HTMLElement>("[style]")?.style.getPropertyValue("--art") ?? "")?.[1];

/** The first word of the shelf, and the first vibe of the release that is a scale: whichever the API gives. */
const FIRST = inShelfOrder(meta.tags)[0] as Tag;
const A_SCALE = meta.tags.find((tag) => tag.shape === "scale" && tag.low_end !== null && tag.high_end !== null) as Tag;
/** The name of an end as a drawing names it. */
const pictureOf = (end: string | null) => `key-${(end ?? "").toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
const picturesBeside = (sentence: HTMLElement) =>
  [...(sentence.parentElement?.querySelectorAll<HTMLElement>("[style]") ?? [])].map(
    (one) => /\/art\/([a-z0-9-]+)\.png/.exec(one.style.getPropertyValue("--art"))?.[1],
  );

describe("the shelf, as the look draws it", () => {
  test("test_the_shelf_is_a_box_and_the_card_of_a_word_is_the_box_in_hand", async () => {
    const { user } = show();
    expect(screen.getByRole("region", { name: SHELF.title })).toHaveAttribute("data-kind", "box");

    await user.click(word(wordOf(FIRST)));

    expect(screen.getByRole("region", { name: FIRST.label })).toHaveAttribute("data-kind", "box-on");
    // The card stands in the shelf, under its words, as it did.
    expect(screen.getByRole("region", { name: SHELF.title })).toContainElement(screen.getByRole("region", { name: FIRST.label }));
  });

  test("test_a_word_has_the_small_drawing_of_its_vibe_beside_it_by_the_id_the_api_gives", async () => {
    const { user } = show();
    await user.click(word(SHELF.more));

    for (const tag of meta.tags) {
      const button = word(wordOf(tag));
      const id = tag.tag_id.replaceAll("_", "-");
      // Every vibe of the made-up city has a drawing of its own, or takes its family's. Its
      // own is named for its id, and for a vibe outright where the name its id gives is
      // that of the thing of a family: a vibe is never drawn by a family that is not its own.
      expect([tag.tag_id, [`thing-${id}`, `thing-vibe-${id}`, `thing-family-${tag.family.replaceAll("_", "-")}`]]).toEqual([
        tag.tag_id,
        expect.arrayContaining([drawingOf(button)]),
      ]);
      // It is the drawing the kit chooses for the vibe, by its id and its family.
      expect([tag.tag_id, drawingOf(button)]).toEqual([tag.tag_id, chosenFor({ kind: "tag", id: tag.tag_id, family: tag.family })]);
      // The drawing is dress. It is kept from a screen reader, and the word names the button.
      expect(button.querySelector("[style]")?.closest("[aria-hidden='true']")).not.toBeNull();
      expect(button).toHaveAccessibleName(wordOf(tag));
    }
  });

  test("test_a_vibe_the_look_has_no_drawing_for_takes_its_familys_and_then_the_plain_one", () => {
    // The data may be of another city, with vibes the look has never heard of.
    const unknown = { ...FIRST, tag_id: "zz_not_drawn" as TagId, shelf_word: "unheard of", shelf_order: 1 };
    const homeless = { ...unknown, tag_id: "zz_nor_this" as TagId, shelf_word: "nor this", family: "zz_no_family" as Tag["family"], shelf_order: 2 };
    render(<Shelf tags={[unknown, homeless]} features={meta.features} open={null} onOpen={() => undefined} onAdd={() => undefined} />);

    expect(drawingOf(word("unheard of"))).toBe(`thing-family-${FIRST.family.replaceAll("_", "-")}`);
    expect(drawingOf(word("nor this"))).toBe("thing-plain");
  });

  test("test_no_name_of_a_vibe_or_of_an_end_is_written_into_the_shelf", () => {
    // A drawing is chosen by what the API gives, and never by a name written here.
    const written = `${readFileSync(path.join(__dirname, "Shelf.tsx"), "utf8")}\n${SHEET}`;
    const names = [
      ...meta.tags.flatMap((tag) => [tag.tag_id, tag.label, tag.low_end, tag.high_end, tag.shelf_word]),
      ...meta.families.map((family) => family.family),
    ].filter((name): name is string => typeof name === "string" && name.length > 3);

    expect(names.length).toBeGreaterThan(30);
    expect(names.filter((name) => new RegExp(`["'\`/-]${name}["'\`.]`, "i").test(written))).toEqual([]);
    expect(/thing-(?!\$)|key-(?!\$)/.test(written)).toBe(false);
  });

  test("test_the_word_that_is_open_is_amber_and_says_that_it_is_open", async () => {
    const { user } = show();
    await user.click(word(wordOf(FIRST)));

    expect(word(wordOf(FIRST))).toHaveAttribute("aria-expanded", "true");
    expect(word(wordOf(FIRST))).not.toHaveAttribute("aria-pressed");
    expect(setsOf('.word[aria-expanded="true"]').get("background-color")).toBe("var(--chosen)");
    expect(setsOf('.word[aria-expanded="true"]').get("color")).toBe("var(--on-chosen)");
    // Amber is not told from cream by everyone: a word has an edge of ink whatever it is.
    expect(setsOf(".word").get("border")).toBe("var(--edge) solid var(--border)");
  });

  test("test_nothing_of_a_word_moves_or_changes_size_under_the_pointer_the_focus_or_a_press", () => {
    const keyed = RULES.filter((rule) => /:(hover|focus|active)/.test(rule.selector) && !/forced-colors/.test(rule.under ?? ""));

    expect(keyed.map((rule) => rule.selector)).toEqual([".word:hover", ".word:focus-visible"]);
    expect([...new Set(keyed.flatMap((rule) => [...rule.sets.keys()]))].sort()).toEqual(["background-color", "box-shadow"]);
    // With the focus it keeps its hard shadow, under the ring that every control has.
    expect(setsOf(".word:focus-visible").get("box-shadow")?.endsWith("var(--box-shadow)")).toBe(true);
    expect(setsOf(".word").get("box-shadow")).toBe("var(--box-shadow)");
  });

  test("test_no_button_of_the_shelf_is_cobalt_for_search_is_in_sight", async () => {
    // A scale with no word of its own asks which end, so its card holds the most buttons.
    const asks = meta.tags.find((tag) => tag.shape === "scale" && tag.shelf_toward === null) as Tag;
    const { user, container } = show();
    await user.click(word(SHELF.more));
    await user.click(word(wordOf(asks)));

    expect(container.querySelectorAll('[data-kind="go"]')).toHaveLength(0);
    expect(RULES.filter((rule) => [...rule.sets.values()].some((value) => /--(accent|cobalt)\b/.test(value)))).toEqual([]);
    // What adds a vibe, what closes its card and what shows more words are buttons of the look.
    for (const name of [SHELF.addToward(asks.low_end ?? ""), SHELF.addToward(asks.high_end ?? ""), SHELF.close, SHELF.fewer]) {
      expect(screen.getByRole("button", { name }).querySelector("[data-kind]")).toHaveAttribute("data-kind", "plain");
    }
  });

  test("test_a_scale_has_the_small_picture_of_each_of_its_ends_beside_the_sentence_that_names_them", async () => {
    const { user } = show();
    await user.click(word(SHELF.more));
    await user.click(word(wordOf(A_SCALE)));
    const said = SHELF.scale(A_SCALE.low_end ?? "", A_SCALE.high_end ?? "");
    const sentence = card(A_SCALE.label).getByText(said);

    // Each by the name the API gives its end, the low end at the left.
    expect(picturesBeside(sentence)).toEqual([pictureOf(A_SCALE.low_end), pictureOf(A_SCALE.high_end)]);
    // The pictures are for the eye, and the sentence is read once.
    for (const picture of sentence.parentElement?.querySelectorAll("[style]") ?? []) {
      expect(picture).toHaveAttribute("aria-hidden", "true");
    }
    expect(sentence.parentElement?.textContent).toBe(said);
  });

  test("test_the_pictures_of_the_two_ends_stand_at_either_hand_of_their_sentence_on_every_screen", async () => {
    // Seen on a phone: the two pictures and the sentence between them were wider than the
    // card, and the picture of the high end went under the picture of the low end, on a line
    // of its own. The sentence is what gives: it runs on between the two, as wide as is left.
    const { user } = show();
    await user.click(word(SHELF.more));
    await user.click(word(wordOf(A_SCALE)));
    const sentence = card(A_SCALE.label).getByText(SHELF.scale(A_SCALE.low_end ?? "", A_SCALE.high_end ?? ""));

    expect([sentence.tagName, sentence.className]).toEqual(["SPAN", "between"]);
    expect(sentence.parentElement?.className).toBe("ends");
    expect(setsOf(".ends").get("display")).toBe("flex");
    expect(setsOf(".ends").get("flex-wrap")).toBe("nowrap");
    expect([setsOf(".between").get("flex"), setsOf(".between").get("min-width")]).toEqual(["0 1 auto", "0"]);
    // A picture is never made narrower for it. A drawing is shown at its own size, and is
    // drawn in a span as the sentence is: so the rule names the sentence, and no element.
    const pictures = [...(sentence.parentElement?.children ?? [])].filter((part) => part !== sentence);
    expect(pictures.map((picture) => [picture.tagName, picture.className])).toEqual([
      ["SPAN", "art"],
      ["SPAN", "art"],
    ]);
    const art = rulesOf(readFileSync(path.join(__dirname, "..", "kit", "Art", "Art.module.css"), "utf8"));
    expect(art.filter((rule) => rule.selector === ".art").map((rule) => rule.sets.get("flex"))).toEqual(["none"]);
    const narrowed = RULES.filter((rule) => /^\.ends\b/.test(rule.selector) && /\b(span|\*)\b/.test(rule.selector.replace(/^\.ends/, "")));
    expect(narrowed.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_a_vibe_that_runs_one_way_has_no_picture_of_an_end_for_it_names_none", async () => {
    const oneWay = meta.tags.find((tag) => tag.shape !== "scale") as Tag;
    const { user } = show();
    await user.click(word(SHELF.more));
    await user.click(word(wordOf(oneWay)));

    const pictures = [...screen.getByRole("region", { name: oneWay.label }).querySelectorAll<HTMLElement>("[style]")];
    expect(pictures.filter((one) => /\/art\/key-/.test(one.style.getPropertyValue("--art")))).toEqual([]);
  });

  test("test_an_end_the_look_has_no_picture_for_takes_the_blank_one", async () => {
    const scale = { ...A_SCALE, low_end: "Unheard of", high_end: "Nor this", shelf_word: "a word" };
    const user = userEvent.setup({ delay: null });
    function HeldOpen() {
      const [open, setOpen] = useState<TagId | null>(null);
      return <Shelf tags={[scale]} features={meta.features} open={open} onOpen={setOpen} onAdd={() => undefined} />;
    }
    render(<HeldOpen />);
    await user.click(word("a word"));

    const sentence = card(scale.label).getByText(SHELF.scale("Unheard of", "Nor this"));
    expect(picturesBeside(sentence)).toEqual(["key-blank", "key-blank"]);
  });

  test("test_what_must_be_read_before_a_vibe_is_added_is_drawn_as_a_notice_in_ink_on_cream", () => {
    for (const note of [".waits", ".crime"]) {
      expect([note, setsOf(note).get("background"), setsOf(note).get("color")]).toEqual([note, "var(--info-bg)", "var(--info-text)"]);
      expect([note, setsOf(note).get("border")]).toEqual([note, "var(--edge) solid var(--notice-edge)"]);
      // The band of amber is inside the rule of ink, and takes no room.
      expect([note, setsOf(note).get("box-shadow")]).toEqual([note, "inset calc(var(--px) * 2) 0 0 var(--notice-mark)"]);
    }
  });

  test("test_the_name_of_a_vibe_is_in_the_face_of_names_and_what_is_read_of_it_in_the_face_of_sentences", () => {
    expect(setsOf(".name").get("font")).toBe("400 var(--name-2) / 1.1 var(--font-name)");
    expect(setsOf(".says").get("font")).toBe("700 var(--size-body) / 1.3 var(--font-say)");
    // No other rule names a face: what is read takes the face of the page.
    const faces = RULES.filter((rule) => rule.sets.has("font") || rule.sets.has("font-family"));
    expect(faces.map((rule) => rule.selector)).toEqual([".says", ".name"]);
  });

  test("test_nothing_that_holds_words_has_a_fixed_height", () => {
    const fixed = RULES.filter((rule) => rule.sets.has("height") || rule.sets.has("max-height"));

    // But the mark of a line of a list and the swatch of a band, which hold none.
    expect([...new Set(fixed.map((rule) => rule.selector))]).toEqual([".recipe li::before", ".cannot li::before", ".swatch"]);
  });

  test("test_what_parts_two_parts_of_the_shelf_is_a_whole_rule_of_sand_and_nothing_is_dashed", () => {
    // The founder: "The dashed border is not understood to a user, please make solid". A
    // rule that parts two parts is there for the eye to run along, and is of sand.
    for (const part of [".apart", ".small"]) {
      expect([part, setsOf(part).get("border-block-start")]).toEqual([part, "var(--edge) solid var(--sand)"]);
    }
    expect(SHEET).not.toMatch(/dashed|dotted/);
  });
});
