import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { METHODS } from "@/content/methods";
import { SITE } from "@/content/site";
import { recordedAnswer } from "@/lib/api/recorded";
import { paths } from "@/lib/paths";

import { faultsIn } from "../../../test/support/axe";
import { asWritten } from "../../../test/support/contrast";
import { rulesOf } from "../../../test/support/css";
import { MethodsTables } from "../MethodsTables/MethodsTables";
import { overTheFoot, WORDS_IN_THE_FOOT } from "../SiteHeader/look";
import { SiteFooter } from "./SiteFooter";

const { meta, data } = recordedAnswer("get_meta", "meta").body;
const RULES = rulesOf(readFileSync(path.join(__dirname, "SiteFooter.module.css"), "utf8"));
const setsOf = (selector: string) =>
  new Map(RULES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

describe("the foot", () => {
  test("test_the_links_and_what_is_said_of_the_data_stand_in_one_box", () => {
    render(<SiteFooter meta={meta} />);

    const foot = screen.getByRole("contentinfo");
    const box = foot.firstElementChild as HTMLElement;

    expect(foot.children).toHaveLength(1);
    expect(box).toHaveAttribute("data-kind", "box");
    expect(within(box).getByRole("navigation", { name: SITE.footerLabel })).toBeInTheDocument();
    expect(within(box).getAllByRole("link").map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      [SITE.nav.vibes, "/vibes"],
      [SITE.nav.methods, "/methods"],
      [SITE.nav.sources, "/sources"],
      [SITE.privacy, "/methods#words"],
    ]);
    // The founder: "get rid of the accessibility tab". It is gone from the foot as from the board.
    expect(within(box).queryByRole("link", { name: /accessib/i })).toBeNull();
    expect(within(box).getByText(SITE.footer.release)).toBeInTheDocument();
    expect(within(box).getByText(SITE.footer.engine)).toBeInTheDocument();
  });

  test("test_the_box_brings_its_own_ground_and_the_foot_lays_none_over_it", () => {
    const laid = RULES.filter((rule) => /^\.(footer|inner)$/.test(rule.selector) && (rule.sets.has("background") || rule.sets.has("overflow")));

    expect(laid.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_release_and_the_engine_are_said_as_they_were_served_each_under_its_name", () => {
    render(<SiteFooter meta={{ ...meta, release_id: "lon-2027-01-20-01", engine_version: "2.0.1" }} />);

    const said = [...screen.getByRole("contentinfo").querySelectorAll("dl > div")].map((one) => [
      one.querySelector("dt")?.textContent,
      one.querySelector("dd")?.textContent,
    ]);

    expect(said).toEqual([
      [SITE.footer.release, "lon-2027-01-20-01"],
      [SITE.footer.engine, "2.0.1"],
    ]);
  });

  test("test_an_id_is_read_out_so_it_is_set_in_the_reading_face_and_a_link_is_a_label_in_the_face_of_names", () => {
    const faces = RULES.filter((rule) => [...rule.sets.keys()].some((property) => /^font(-family)?$/.test(property)));

    // Only a link is set in the face of names. What is said of the data takes the face of a sentence.
    expect(faces.map((rule) => [rule.selector, rule.sets.get("font")])).toEqual([
      [".link", "400 var(--name-1) / 1 var(--font-name)"],
    ]);
    expect(setsOf(".link").get("font-synthesis")).toBe("none");
    expect(setsOf(".release").get("font-size")).toBe("var(--size-small)");
    // An id has no gap to break at. It is broken where it must be, and the page is never wider for it.
    expect(setsOf(".release dd").get("overflow-wrap")).toBe("anywhere");
  });

  test("test_the_foot_is_the_calmest_part_of_a_page_and_no_link_of_it_is_drawn_as_a_button", () => {
    render(<SiteFooter meta={meta} />);

    for (const link of within(screen.getByRole("contentinfo")).getAllByRole("link")) {
      expect(link).toHaveClass("target");
      expect(link.getAttribute("style")).toBeNull();
    }
    expect(RULES.filter((rule) => rule.sets.has("border-image") || rule.sets.has("box-shadow")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_foot_has_no_accessibility_fault", async () => {
    const { container } = render(<SiteFooter meta={meta} burro={false} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the way from the foot to what is said of what a person types", () => {
  const theWay = () => within(screen.getByRole("contentinfo")).getByRole("link", { name: new RegExp(METHODS.words.title) });

  test("test_the_foot_leads_to_how_a_persons_words_are_handled_by_a_name_a_person_looks_for_at_the_foot_of_a_page", () => {
    // The founder asked for the link and the lines under the search box to go. What is said
    // of what a person types is said where it was, among the methods, and the foot of every
    // page leads to it.
    render(<SiteFooter meta={meta} />);

    expect(WORDS_IN_THE_FOOT).toBe("privacy");
    expect(SITE.privacy).toBe("Privacy");
    expect(theWay().textContent).toBe(SITE.privacy);
    // To whoever hears the page it says where it leads as well, in the words that head that
    // part: what is seen of it is the start of its name.
    expect(theWay()).toHaveAccessibleName("Privacy: How your words are handled");
    expect(theWay()).toHaveAccessibleName(`${SITE.privacy}: ${METHODS.words.title}`);
    expect(theWay().getAttribute("aria-label")?.startsWith(theWay().textContent ?? "no words")).toBe(true);
    expect(theWay()).toHaveAttribute("href", paths.methods("words"));
    expect(theWay().getAttribute("href")).toBe("/methods#words");
  });

  test("test_it_is_a_link_of_the_foot_as_every_other_is_and_stands_last_among_them", () => {
    render(<SiteFooter meta={meta} />);
    const links = within(screen.getByRole("navigation", { name: SITE.footerLabel })).getAllByRole("link");

    expect(links.at(-1)).toBe(theWay());
    expect(links).toHaveLength(4);
    expect(theWay().tagName).toBe("A");
    expect(theWay()).toHaveClass("target");
    // Which page a person reads next is told to no server ahead of time.
    expect(theWay()).toHaveAttribute("data-prefetch", "false");
    expect(theWay().getAttribute("style")).toBeNull();
    expect(theWay().className).toBe(links[0]?.className);
  });

  test("test_the_part_it_leads_to_is_on_the_page_of_methods_under_the_heading_it_is_named_for", () => {
    render(<MethodsTables meta={data} />);

    const heading = document.getElementById(paths.methods("words").split("#")[1] ?? "no part");

    expect(heading?.tagName).toBe("H2");
    expect(heading?.textContent).toBe(METHODS.words.title);
    // What is typed, where it goes, and that it is not kept: each is said there.
    const part = heading?.parentElement;
    expect(part).toHaveTextContent("What you type is sent to Burro to be read, and Burro does not keep it.");
    expect(part).toHaveTextContent("It is never put in a web address.");
    expect(part).toHaveTextContent(data.reader.notice);
    // It stands in the fold of the methods, which a link that names the part opens.
    expect(heading?.closest("details")).not.toBeNull();
  });

  test("test_one_line_names_it_by_the_heading_of_the_part_it_leads_to", () => {
    render(<SiteFooter meta={meta} words="as-headed" />);

    expect(theWay().textContent).toBe(METHODS.words.title);
    expect(theWay()).toHaveAccessibleName(METHODS.words.title);
    expect(theWay()).not.toHaveAttribute("aria-label");
    expect(theWay()).toHaveAttribute("href", "/methods#words");
  });

  test.each(["privacy", "as-headed"] as const)("test_the_foot_has_no_accessibility_fault_named_either_way: %s", async (words) => {
    const { container } = render(<SiteFooter meta={meta} words={words} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("Burro over the foot", () => {
  const NARROW = /max-width:\s*39\.99rem/;
  const his = () => [...screen.getByRole("contentinfo").querySelectorAll<HTMLElement>("[data-pose]")];
  const under = (selector: string, media: RegExp | null) =>
    new Map(
      RULES.filter((rule) => rule.selector === selector && (media === null ? rule.under === null : media.test(rule.under ?? ""))).flatMap((rule) => [
        ...rule.sets,
      ]),
    );
  const OF_HIM = RULES.filter((rule) => /\.burro\b/.test(rule.selector));

  test("test_left_to_itself_the_foot_draws_him_so_that_he_is_on_every_page_of_a_narrow_screen", () => {
    // The name board of a phone is one line, which the name and its pages hold. So on a
    // narrow screen he is drawn over the foot, which every page has.
    expect(overTheFoot()).toBe(true);
    render(<SiteFooter meta={meta} />);
    const foot = screen.getByRole("contentinfo");
    const [he, ...others] = his();

    expect(others).toEqual([]);
    expect([he?.getAttribute("data-pose"), he?.getAttribute("data-peeps"), he?.getAttribute("data-stage")]).toEqual(["sits", "true", "false"]);
    // He is in the box of the foot, which is the one thing the foot holds, and so inside
    // what a screen reader knows as the foot of the page. He comes first in it, as he is
    // seen first, over its head.
    expect(foot.children).toHaveLength(1);
    expect(he?.parentElement).toBe(foot.firstElementChild?.firstElementChild);
    // He stirs, and nothing stands by him to be pressed: a keyboard comes to the links of the
    // foot and to nothing of him, and the whole of him is kept from a screen reader.
    expect(he?.querySelector("[data-moves]")).toHaveAttribute("data-moves", "true");
    expect(within(foot).queryByRole("button")).toBeNull();
    const reached = [...foot.querySelectorAll("a, button, input, [tabindex]")].map((one) => one.getAttribute("aria-label") ?? one.textContent);
    expect(reached).toEqual([SITE.nav.vibes, SITE.nav.methods, SITE.nav.sources, `${SITE.privacy}: ${METHODS.words.title}`]);
    expect(he).toHaveAttribute("aria-hidden", "true");
    expect(he?.textContent).toBe("");
    expect(he?.closest("a")).toBeNull();
  });

  test("test_one_line_takes_him_off_the_foot_which_then_holds_what_it_held", () => {
    render(<SiteFooter meta={meta} burro={false} />);
    const foot = screen.getByRole("contentinfo");

    expect(his()).toEqual([]);
    expect(within(foot).queryByRole("button")).toBeNull();
    expect([...(foot.firstElementChild?.children ?? [])].map((one) => one.tagName)).toEqual(["NAV", "DL"]);
  });

  test("test_he_sits_behind_the_rule_at_the_head_of_the_foot_and_takes_no_room", () => {
    const drawn = under(".burro", NARROW);

    // He is laid over the grass that parts the page from the foot, and takes no room: the
    // foot is as high with him as without him. Measured in a browser at 320, 360, 390 and
    // 639 wide: the foot and the page each stood where they stood without him.
    expect(drawn.get("position")).toBe("absolute");
    expect(drawn.get("display")).toBe("block");
    // His box ends where the rule of the box begins, which is drawn four art pixels over
    // what the box holds: he is seen from his back up, and the rule hides the rest of him.
    expect(drawn.get("inset-block-end")).toBe("calc(100% + var(--px) * 4)");
    expect((asWritten()["--frame-box-wide"] ?? "").split(/\s+(?![^(]*\))/)[0]).toBe("calc(var(--px) * 4)");
    // He stands in from the far side of the foot, clear of its corner.
    expect(drawn.get("inset-inline-end")).toBe("var(--space-5)");
    // No size is set for him: he is as large as he is drawn.
    const sized = OF_HIM.filter((rule) => [...rule.sets.keys()].some((property) => /^((min|max)-)?(width|height)$/.test(property)));
    expect(sized.map((rule) => rule.selector)).toEqual([]);
    // Nothing of the foot is laid out for him, and no ground is laid: he brings his own.
    expect(OF_HIM.filter((rule) => rule.sets.has("background") || rule.sets.has("margin") || rule.sets.has("padding")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_on_a_wider_screen_the_name_board_draws_him_and_the_foot_does_not", () => {
    // From 40rem the board has room for him. The two never draw him at one width: the foot
    // draws him under 40rem, and the board from it.
    expect([...under(".burro", null)]).toEqual([["display", "none"]]);
    expect(OF_HIM.filter((rule) => rule.sets.get("display") === "block").map((rule) => rule.under)).toEqual(["@media (max-width: 39.99rem)"]);
    const board = rulesOf(readFileSync(path.join(__dirname, "../SiteHeader/SiteHeader.module.css"), "utf8")).filter(
      (rule) => rule.selector === ".burro" && rule.sets.get("display") === "block",
    );
    expect(board.map((rule) => rule.under)).toEqual(["@media (min-width: 40rem)"]);
  });

  test("test_where_he_is_drawn_on_the_page_he_is_not_drawn_over_the_foot_as_well", () => {
    // He is one rabbit. Before a search he sits beside the heading, and while a search is
    // read he hops where the answer will stand. Where what holds him in the page is not
    // drawn on a narrow screen, `data-room="wide"`, he is not seen there, and the foot draws him.
    const gone = OF_HIM.filter((rule) => /:has\(main\b/.test(rule.selector));

    expect(gone.map((rule) => [rule.under, rule.selector, [...rule.sets]])).toEqual([
      ["@media (max-width: 39.99rem)", ':global(body):has(main :not([data-room="wide"]) > [data-pose]) .burro', [["display", "none"]]],
    ]);
    expect(OF_HIM.filter((rule) => rule.sets.has("visibility") || rule.sets.has("opacity")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_foot_has_no_accessibility_fault_with_him_over_it", async () => {
    const { container } = render(<SiteFooter meta={meta} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
