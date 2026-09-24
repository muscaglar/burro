import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";

import { CRIME_ACCOUNT, CRIME_RULE } from "@/content/crime";
import { READING } from "@/content/labels";
import { LEGEND } from "@/content/map";
import { SHELF, STRIP } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations, Tag, TagId } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { faultsIn } from "../../../test/support/axe";
import { problemsWith } from "../../../test/support/contract";
import { isFor, rulesOf } from "../../../test/support/css";
import { figuresNotFrom } from "../../../test/support/figures";
import { watch } from "../../../test/support/watch";
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
}

/** The shelf, held as the page holds it: the page says which card is open. */
function Held({ told, form = meta, withTheCity = true }: Shown) {
  const [open, setOpen] = useState<TagId | null>(null);
  return (
    <Shelf
      tags={form.tags}
      features={form.features}
      open={open}
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

function show(form = meta, withTheCity = true) {
  const told = { added: [] as Operations[], opened: [] as (TagId | null)[] };
  const view = render(<Held told={told} form={form} withTheCity={withTheCity} />);
  return { ...told, user: userEvent.setup({ delay: null }), ...view };
}

const shelf = () => within(screen.getByRole("region", { name: SHELF.title }));
const word = (name: string) => shelf().getByRole("button", { name });
const card = (name: string) => within(screen.getByRole("region", { name }));

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
    expect(unworded.map((tag) => tag.tag_id).sort()).toEqual(["family_amenities", "foodie", "homes", "street_character"]);
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
    const recipe = within(opened.getByRole("heading", { name: SHELF.recipe }).nextElementSibling as HTMLElement);
    expect(recipe.getAllByRole("listitem").map((part) => part.textContent)).toEqual(
      pace.terms.map((term) => {
        const metric = meta.features.find((one) => one.feature_id === term.feature_id);
        return `${SHELF.share(term.hundredths)} ${metric?.label}${READING[term.reading]}`;
      }),
    );
    expect(pace.terms.reduce((sum, term) => sum + term.hundredths, 0)).toBe(100);
    const cannot = within(opened.getByRole("heading", { name: SHELF.cannotSee }).nextElementSibling as HTMLElement);
    expect(cannot.getAllByRole("listitem").map((line) => line.textContent)).toEqual(pace.cannot_see);
    expect(pace.cannot_see.length).toBeGreaterThan(1);
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
    expect(before(add, opened.getByRole("heading", { name: SHELF.recipe }))).toBe(true);
    expect(before(add, opened.getByRole("heading", { name: SHELF.cannotSee }))).toBe(true);
  });

  test("test_on_a_narrow_screen_a_card_that_opens_is_brought_to_the_top_of_the_screen", async () => {
    const brought: ScrollIntoViewOptions[] = [];
    Element.prototype.scrollIntoView = function scrollIntoView(how?: boolean | ScrollIntoViewOptions) {
      if (typeof how === "object") brought.push(how);
    };
    const narrow = (matches: boolean) => {
      window.matchMedia = ((query: string) => ({ matches: /max-width/.test(query) ? matches : false, media: query })) as never;
    };
    try {
      narrow(true);
      const { user } = show();
      await user.click(word("leafy"));
      expect(brought).toEqual([{ block: "start", behavior: "smooth" }]);

      // On a wide screen the card and the map are both in sight, and nothing moves.
      narrow(false);
      await user.click(word("lively"));
      expect(brought).toHaveLength(1);
    } finally {
      delete (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView;
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
