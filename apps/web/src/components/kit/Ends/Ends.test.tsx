import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { recordedAnswer } from "@/lib/api/recorded";
import { endsOf } from "@/lib/vibes";

import { faultsIn } from "../../../../test/support/axe";
import { rulesOf } from "../../../../test/support/css";
import { pictureOf } from "../drawings";
import { Ends } from "./Ends";
import { NO_PICTURE, picturesAtEnds } from "./picture";

const STYLES = rulesOf(readFileSync(path.join(__dirname, "Ends.module.css"), "utf8"));
const picturesOf = (container: HTMLElement) =>
  [...container.querySelectorAll<HTMLElement>(".art")].map((one) => one.style.getPropertyValue("--art"));

/** A vibe of the release, which no test names: the first the service gives. */
function aVibe() {
  const [first] = recordedAnswer("get_meta", "meta").body.data.tags;
  if (first === undefined) throw new Error("The recorded release holds no vibe.");
  return first;
}

describe("the two ends of a scale", () => {
  test("test_each_end_has_its_small_picture_and_its_name_and_the_low_end_is_at_the_left", () => {
    const { container } = render(<Ends low="Houses" high="Flats" />);

    expect(picturesOf(container)).toEqual(['url("/art/key-houses.png")', 'url("/art/key-flats.png")']);
    expect([...container.querySelectorAll(".name")].map((name) => name.textContent)).toEqual(["Houses", "Flats"]);
  });

  test("test_the_names_are_read_and_the_pictures_are_for_the_eye", () => {
    const { container } = render(<Ends low="Calm" high="Buzzy" />);

    expect(screen.getByText("Calm").closest("[aria-hidden]")).toBeNull();
    expect(screen.getByText("Buzzy").closest("[aria-hidden]")).toBeNull();
    for (const picture of container.querySelectorAll(".art")) expect(picture).toHaveAttribute("aria-hidden", "true");
    expect(screen.queryByRole("img")).toBeNull();
    // A name is read: it is set in the reading face.
    expect(STYLES.filter((rule) => rule.selector === ".name").map((rule) => rule.sets.get("font"))).toEqual([
      "400 var(--size-small) / 1.1 var(--font-say)",
    ]);
  });

  test("test_a_vibe_that_runs_one_way_runs_from_least_to_most", () => {
    const { container } = render(<Ends low={null} high={null} />);

    expect(picturesOf(container)).toEqual(['url("/art/key-least.png")', 'url("/art/key-most.png")']);
    expect([...container.querySelectorAll(".name")].map((name) => name.textContent)).toEqual(["least", "most"]);
  });

  test("test_an_end_with_no_picture_takes_the_blank_one_and_keeps_its_name", () => {
    const { container } = render(<Ends low="An end of a later release" high="Another" />);

    expect(picturesOf(container)).toEqual(['url("/art/key-blank.png")', 'url("/art/key-blank.png")']);
    expect(screen.getByText("An end of a later release")).toBeInTheDocument();
    expect(screen.getByText("Another")).toBeInTheDocument();
  });

  test("test_with_the_id_of_its_vibe_each_end_has_the_one_picture_that_is_drawn_for_that_end", () => {
    const vibe = aVibe();
    const { container } = render(<Ends id={vibe.tag_id} low={vibe.low_end} high={vibe.high_end} />);

    expect(picturesOf(container)).toEqual(picturesAtEnds(vibe.tag_id).map((name) => `url("${pictureOf(name)}")`));
    expect(picturesAtEnds(vibe.tag_id)).not.toContain(NO_PICTURE);
    // The names are the service's still, and "least" and "most" of a vibe that runs one way.
    expect([...container.querySelectorAll(".name")].map((name) => name.textContent)).toEqual(endsOf(vibe));
  });

  test("test_every_vibe_of_the_release_has_two_pictures_that_are_opposites_whichever_way_it_runs", () => {
    const vibes = recordedAnswer("get_meta", "meta").body.data.tags;

    expect(new Set(vibes.map(({ shape }) => shape))).toEqual(new Set(["scale", "one_way"]));
    for (const vibe of vibes) {
      const { container, unmount } = render(<Ends id={vibe.tag_id} low={vibe.low_end} high={vibe.high_end} />);
      const [low, high] = picturesOf(container);

      expect([vibe.tag_id, low === high, [low, high].includes(`url("${pictureOf(NO_PICTURE)}")`)]).toEqual([vibe.tag_id, false, false]);
      // One picture at each end, and no more.
      expect([vibe.tag_id, container.querySelectorAll(".end .art").length]).toEqual([vibe.tag_id, 2]);
      unmount();
    }
  });

  test("test_a_vibe_that_nobody_has_drawn_has_the_blank_one_at_both_ends_and_keeps_their_names", () => {
    const { container } = render(<Ends id="a_vibe_of_a_later_release" low="One end" high="The other" />);

    expect(picturesOf(container)).toEqual([NO_PICTURE, NO_PICTURE].map((name) => `url("${pictureOf(name)}")`));
    expect([...container.querySelectorAll(".name")].map((name) => name.textContent)).toEqual(["One end", "The other"]);
  });

  test("test_what_runs_between_the_two_ends_stands_between_them", () => {
    const { container } = render(
      <Ends low="Calm" high="Buzzy">
        <input type="range" aria-label="Going out" />
      </Ends>,
    );
    const parts = [...(container.firstElementChild?.children ?? [])].map((part) => part.className);

    expect(parts).toEqual(["end", "between", "end"]);
    expect(container.querySelector(".between input")).not.toBeNull();
  });

  test("test_with_nothing_between_them_the_two_ends_stand_side_by_side", () => {
    const { container } = render(<Ends low="Calm" high="Buzzy" />);

    expect([...(container.firstElementChild?.children ?? [])].map((part) => part.className)).toEqual(["end", "end"]);
  });

  test("test_neither_end_is_the_good_one_so_the_two_are_drawn_alike", () => {
    const { container } = render(<Ends low="Calm" high="Buzzy" />);
    const [low, high] = [...container.querySelectorAll(".end")];
    const shape = (end: Element | undefined) =>
      [...(end?.querySelectorAll("*") ?? [])].map((part) => [part.tagName, part.className, [...part.attributes].map((one) => one.name).sort()]);

    // The same parts, in the same order, of the same classes: one rule draws both.
    expect(shape(low)).toEqual(shape(high));
    expect(STYLES.filter((rule) => /:(first|last|nth)-/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <p>
        <Ends low="Houses" high="Flats" />
        <Ends low={null} high={null}>
          <span>between</span>
        </Ends>
      </p>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
