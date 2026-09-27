"use client";

import { useId, useState, type ReactNode } from "react";

import { whyRefused } from "@/content/search";
import { CRIME_ACCOUNT, countsOf, crimeVibes } from "@/content/crime";
import {
  BRANDS,
  CRIME,
  CRIME_CAVEAT,
  FEATURES,
  HIDDEN,
  JOURNEY,
  KIND_OF_SEARCH,
  SETTINGS,
  SLIDER,
} from "@/content/settings";
import type { Answer } from "@/lib/api/client";
import type { Handed } from "@/lib/api/handed";
import type {
  AreaSummary,
  FoundPlace,
  Metric,
  Operations,
  PlacesData,
  PreferenceSpec,
  RejectReason,
  Tenure,
} from "@/lib/api/schema";
import { recipeOf } from "@/lib/holds";
import { namesOfPlaces } from "@/lib/search/chips";
import { counts } from "@/lib/search/counts";
import { edits, merged, NO_EDITS } from "@/lib/search/edits";

import { Disclosure } from "../Disclosure/Disclosure";
import { Frame } from "../kit/Frame/Frame";
import { Press } from "../kit/Press/Press";
import { holdsAFigure } from "../kit/reads";
import { Drawn } from "../kit/Thing/Thing";
import { PlaceCombobox } from "../PlaceCombobox/PlaceCombobox";
import { BudgetControl } from "./BudgetControl";
import { CommuteControl, JourneySettings } from "./CommuteControl";
import {
  groupsOf,
  hasBegun,
  heldBy,
  isOfAPrice,
  madeOf,
  offeredTo,
  ofFamily,
  openAtFirst,
  saidOfTheUsual,
  type FoldKey,
  type Group,
  type GroupKey,
} from "./groups";
import { useHeldInPlace } from "./held";
import { NAMED_IN_SIGHT, SAYS_AT_THEIR_HEAD } from "./look";
import { useChosen } from "./opened";
import styles from "./SettingsPanel.module.css";
import { TenureChoice } from "./TenureChoice";
import { MadeOf, VibeControl } from "./VibeControl";
import { WeightControl } from "./WeightControl";

interface Props {
  /** The spec the API last returned. Every control is drawn from it. */
  readonly spec: PreferenceSpec;
  readonly meta: Handed;
  readonly areas: readonly AreaSummary[];
  readonly placeNames: Readonly<Record<string, string>>;
  readonly onEdit: (operations: Operations) => void;
  /** Told of a choice of renting, buying or visiting. Before anything is asked for, it sends nothing. */
  readonly onTenure: (tenure: Tenure) => void;
  /** Route 8, for the field that adds a place to reach. */
  readonly searchPlaces: (text: string, signal: AbortSignal) => Promise<Answer<PlacesData>>;
  readonly onAddPlace: (place: FoundPlace) => void;
  /** Said in place of the field when no more places can be named. */
  readonly full?: string | null;
  /** Changes with every answer from the API. */
  readonly version: number;
  /** Why the last edit to a part was not taken, by part. */
  readonly refused?: ReadonlyMap<string, RejectReason>;
  /**
   * The parts whose change has not been answered, where no answer can come, and what the
   * page says of that. Each control of such a part says it where it stands.
   */
  readonly unsent?: { readonly parts: ReadonlySet<string>; readonly says: string } | null;
  readonly open: boolean;
  readonly onToggle: (open: boolean) => void;
  /** Ranks the settings as they stand. Left out once there is a ranking. */
  readonly onRank?: () => void;
  readonly busy?: boolean;
  /**
   * True where the settings stand open beside the answer, as they do on a wide screen. No
   * button opens them there, so `open` says nothing and `onToggle` is told nothing: they
   * stand under a heading that names them, and the page can give them the focus.
   */
  readonly standing?: boolean;
  /**
   * Whether a search is open, where the page says so. Before one the settings gather what
   * is chosen, and the button that stands under them ranks by it. Once one is open a
   * change is ranked as it is made. They say which is so, and stand as each asks. Left
   * out, they tell it from the spec: a search is open once the spec is one the API returned.
   */
  readonly begun?: boolean;
}

/**
 * What stands open unless a person says otherwise, and the search it was worked out for:
 * the spec, the count of answers when it was the search, and whether a search was open.
 */
interface AtFirst {
  readonly spec: PreferenceSpec;
  readonly version: number;
  readonly begun: boolean;
  readonly open: ReadonlySet<FoldKey>;
}

/**
 * True while the focus is on what a group holds: a person is in the settings. The bar of a
 * group is none of what it holds, and stays where it is whatever opens or closes. It is
 * asked of the page as the search changes, and is kept nowhere: what had the focus may
 * have gone from the page since, and a browser does not say so.
 */
function isInAGroup(stack: string): boolean {
  if (typeof document === "undefined") return false;
  const [groups, on] = [document.getElementById(stack), document.activeElement];
  if (groups === null || on === null || !groups.contains(on)) return false;
  // A group is a child of the stack, and its bar a child of the group.
  return on !== groups && on.parentElement !== groups && on.parentElement?.parentElement !== groups;
}

/**
 * The settings: the same search as a form, in groups that fold, one under
 * the other. They first ask what the search is for: a home to rent, a home to
 * buy, or somewhere to stay on a visit. A visit holds no budget, no number of
 * bedrooms and no kind of home, so none is drawn while it is chosen, nor any
 * measurement of a price in any group: what is left is where a visitor needs
 * to get to, and what they want around them.
 *
 * Money and journeys first, then one group for each family of
 * vibes, as the API names and orders them, then the brands, then what belongs
 * to no family, and recorded crime last. Every control here makes the edit a
 * sentence would, so the page works with no words read at all.
 *
 * In a family each vibe has one slider, and a fold under it opens what it is
 * made of. It stands open where the search holds a part of the vibe by
 * itself, which the bar of the group names: what a person asked for, and what
 * Burro counts in every search. A feature of the family that is in no recipe
 * is under "Other things that count". It offers only what the release can
 * rank, within the limits the API served, so it never offers what the reducer
 * would refuse.
 *
 * THE GROUPS ARE ONE STACK OF BARS, each from one side of the box to the
 * other: the drawing of its thing and its name at one end, its arrow at the
 * other, and between them what it holds that a person asked for, so that what
 * is set is read without opening anything. A group that is open is amber.
 *
 * Before a search the first two are open, so that it is seen that a group
 * opens and closes. Once a search is open every group is closed: a person has
 * the answer before them and came to change one thing, so what is set is read
 * on the bars, on one screen, and the group that is wanted is one press away.
 * `look.ts` has the one line that leaves a couple open then, or every group
 * that holds something asked for. It is worked out again as the search
 * changes elsewhere: as a sentence is read, as a chip is taken off. It is not
 * worked out again for what the settings themselves changed, which would
 * open and close groups under a person's hand, nor while a person is in a
 * group, whatever changed the search: an answer to a sentence may come while
 * they type a number there. What a person opened stays open, and what they
 * closed stays closed, until they start again.
 *
 * They are one press away, behind a button, or they stand open where the
 * page has a place for them. Either way they hold the same groups. Behind
 * their button they are brought into sight as a press opens them, where they
 * would begin under the foot of the window.
 *
 * AT THEIR HEAD STANDS THEIR NAME, AND NO SENTENCE. The tab of Deep search says
 * what it is and which button makes the search, and once a search is open
 * "Refine search" says what they are for: what they said of themselves said it
 * twice, and is gone. What Burro counts in every search that nobody chose is
 * named on the bar of the group that holds each, by the name the API gives
 * it: a result says how many things its fit is based on, and these are the
 * rest of them. Their name stands over them wherever they stand open, and
 * whoever hears the page finds them by it. `look.ts` has the one line that
 * names what Burro counts at their head too, and the one that draws their
 * name before a search alone.
 *
 * NOTHING MOVES UNDER A PRESS. What a switch shows keeps its room while the
 * switch is off, and what the scale of a slider means is said whether or not
 * a thing is on. What is pressed is held where it stands in the window until
 * the answer to it is drawn, whatever the answer changes over it: `held.ts`.
 *
 * They are drawn as Town Map draws a panel: one box, and in it the stack.
 */
export function SettingsPanel({
  spec,
  meta,
  areas,
  placeNames,
  onEdit,
  onTenure,
  searchPlaces,
  onAddPlace,
  full = null,
  version,
  refused = new Map(),
  unsent = null,
  open,
  onToggle,
  onRank,
  busy = false,
  standing = false,
  begun: said,
}: Props) {
  const id = useId();
  const { limits } = meta;
  const names = namesOfPlaces(spec, placeNames);
  const why = (part: string) => {
    const reason = refused.get(part);
    if (reason !== undefined) return whyRefused(reason, meta);
    return unsent?.parts.has(part) === true ? unsent.says : null;
  };
  // A place that is being added is no journey of the search until its answer comes, so no
  // control of a journey is there to say that it waits: the field that found it says so.
  const adding =
    unsent !== null &&
    [...unsent.parts].some(
      (part) => part.startsWith("place:") && !spec.commutes.some((one) => part === `place:${one.place_id}`),
    )
      ? unsent.says
      : null;
  // A visit is a search for somewhere to stay. It holds no budget, no number of bedrooms
  // and no kind of home, and nothing of a price is drawn for it in any group.
  const visiting = spec.tenure === "visit";
  const held = heldBy(meta, spec.tenure);
  const offered = offeredTo(spec.tenure, meta.features);
  const groups = groupsOf(spec, meta, areas, placeNames);

  const begun = said ?? hasBegun(spec, meta);
  const [chosen, choose] = useChosen(begun);
  const [atFirst, setAtFirst] = useState<AtFirst>(() => ({
    spec,
    version,
    begun,
    open: openAtFirst(groups, begun, spec, meta),
  }));
  /**
   * The count of answers when a control of the settings last changed the search. What
   * comes next is the answer to that, and is the settings' own. What comes after it is
   * not: an edit that was refused leaves the search as it was, and is answered all the same.
   */
  const [changedAt, setChangedAt] = useState<number | null>(null);
  // The search changed, was answered, or was opened. Elsewhere: what stands open is what
  // a search leaves open. By these settings, or while a person is in a group of them:
  // nothing opens or closes, which would move what is in a person's hand. What comes
  // while they are there may be the answer to a sentence that was sent before they came:
  // a group that stood open was closed under them as they typed in it, and what they had
  // typed went with it. No control of the settings ends a search: where none is open any
  // more a person started again, and the settings are as they first stood.
  if (atFirst.spec !== spec || atFirst.version !== version || atFirst.begun !== begun) {
    const own = begun && (changedAt === atFirst.version || isInAGroup(`${id}-groups`));
    setAtFirst({ spec, version, begun, open: own ? atFirst.open : openAtFirst(groups, begun, spec, meta) });
  }
  const isOpen = (key: FoldKey) => chosen.get(key) ?? atFirst.open.has(key);

  // What is pressed is held where it stands in the window, from the press until the
  // answer to it is drawn: what stands over it may change by then, as the bar of its group
  // does where it comes to name what was turned on.
  const inHand = useHeldInPlace(version, begun, busy);

  /** What a control of the settings tells the page, which is told first that the change is the settings' own. */
  const here =
    <Told extends readonly unknown[]>(tell: (...told: Told) => void) =>
    (...told: Told) => {
      setChangedAt(version);
      inHand.sent();
      tell(...told);
    };
  const edit = here(onEdit);
  const shared = { limits, onEdit: edit, version };

  /**
   * The kind of search is chosen. It is the page's to send, which before anything is asked
   * for sends nothing. But what the search holds of a price, and counts, is taken off as
   * visiting is chosen, in the one edit that says so: left in, it would go on counting in
   * a visit, with nothing in sight to turn it off by.
   */
  const chooseKind = (kind: Tenure) => {
    const priced =
      kind === "visit"
        ? meta.features.filter(
            (metric) => isOfAPrice(metric) && counts(spec.weights.find((weight) => weight.feature_id === metric.feature_id)),
          )
        : [];
    if (priced.length === 0) here(onTenure)(kind);
    else edit([...priced.map((metric) => edits.featureOff(metric.feature_id)), edits.tenure(kind)].reduce(merged, NO_EDITS));
  };

  /**
   * What is pressed in a group may go with the press: a journey that is removed, an area
   * that is shown again, the field of a place once no more can be named. Each goes when
   * the answer comes, and the focus must not go with it: it is never left on nothing. It
   * is handed to the bar of the group the focus is in, which stays, or where the group
   * itself goes with what it held, to the bar of the group before it. A group is a child of
   * the stack, and its bar a child of the group. The page is not moved for it.
   */
  const handOn = (goes: "held" | "group" = "held", from: Element | null = document.activeElement) => {
    const stack = document.getElementById(`${id}-groups`);
    let group = from;
    while (group !== null && group.parentElement !== stack) group = group.parentElement;
    const stays = goes === "group" ? (group?.previousElementSibling ?? null) : group;
    if (stack !== null) stays?.querySelector<HTMLElement>(":scope > button")?.focus({ preventScroll: true });
  };
  /**
   * A journey that is removed goes with all it holds. The focus goes to what removes the
   * journey beside it, the next or else the one before, which comes to stand where this
   * one stood: and where it was the only journey, to the bar of the journeys.
   */
  const journeyGoes = () => {
    const journey = document.activeElement?.closest("[data-journey]") ?? null;
    const all = [...(journey?.parentElement?.querySelectorAll(":scope > [data-journey]") ?? [])];
    const at = journey === null ? -1 : all.indexOf(journey);
    const beside = (all[at + 1] ?? all[at - 1])?.querySelector<HTMLElement>("[data-removes]");
    if (beside) beside.focus({ preventScroll: true });
    else handOn();
  };

  const controlsOf = (features: readonly Metric[], scale: string) =>
    features.map((metric) => (
      <li key={metric.feature_id}>
        <WeightControl
          {...shared}
          metric={metric}
          weight={spec.weights.find((weight) => weight.feature_id === metric.feature_id)}
          problem={why(`feature:${metric.feature_id}`)}
          scale={scale}
        />
      </li>
    ));

  /**
   * What a group of sliders holds. What the scale of a slider means is said once for the
   * group, where it can be seen, wherever the group holds a slider or the room of one. It
   * is said whether or not a thing of the group is on: said only once one was, it was
   * drawn over all the group holds as the first was turned on, and what was pressed went
   * a line down the page from under the press.
   */
  const sliding = (scale: string, slides: boolean, children: ReactNode) => (
    <div className={styles.inside}>
      {slides ? (
        <p id={scale} className={styles.hint}>
          {SLIDER.range}
        </p>
      ) : null}
      {children}
    </div>
  );

  /**
   * What each group holds, by its key, given the id of the line that says what its scale
   * means. It is drawn only while the group is open.
   */
  const inside = new Map<GroupKey, (scale: string) => ReactNode>();

  inside.set("money", () => (
    <div className={styles.inside}>
      <TenureChoice tenure={spec.tenure} onChoose={chooseKind} version={version} problem={why("tenure")} />
      {visiting ? (
        <p className={styles.told}>{KIND_OF_SEARCH.noBudget}</p>
      ) : (
        <BudgetControl
          {...shared}
          budget={spec.budget}
          tenure={spec.tenure}
          problem={why("budget")}
          costs={meta.holds.costs}
        />
      )}
    </div>
  ));

  inside.set("journeys", () => (
    <div className={styles.inside}>
      {/* Where the data names no place, there is none to add, and the group says so. */}
      {meta.holds.journeys ? (
        <>
          <PlaceCombobox
            search={searchPlaces}
            onPick={(place) => {
              // The field gives way to the line that says no more can be named, once the
              // place that was picked is the last that can be.
              if (spec.commutes.length + 1 >= limits.max_commutes) handOn();
              here(onAddPlace)(place);
            }}
            full={full}
          />
          {adding ? (
            <p className={styles.problem} role="alert">
              {adding}
            </p>
          ) : null}
        </>
      ) : (
        <p className={styles.hint}>{JOURNEY.notInData}</p>
      )}
      {meta.holds.journeys && spec.commutes.length === 0 ? <p className={styles.hint}>{JOURNEY.none}</p> : null}
      {spec.commutes.map((commute) => (
        <CommuteControl
          {...shared}
          key={commute.place_id}
          commute={commute}
          name={names.get(commute.place_id) ?? ""}
          problem={why(`place:${commute.place_id}`)}
          onEdit={(operations) => {
            if (operations.commute_ops.some((one) => one.action === "remove")) journeyGoes();
            edit(operations);
          }}
        />
      ))}
      {spec.commutes.length > 0 ? <JourneySettings {...shared} spec={spec} problem={why("journeys")} /> : null}
    </div>
  ));

  for (const { family, vibes, others } of held.families) {
    // A vibe that runs one way always shows its slider, where any area can be placed on it,
    // and a thing that is off keeps the room of its slider. A scale says what its own ends mean.
    const slides =
      vibes.some((tag) => tag.shape === "one_way" && recipeOf(meta, tag.tag_id)?.placed !== false) ||
      others.length > 0;
    inside.set(ofFamily(family), (scale) =>
      sliding(
        scale,
        slides,
        <>
          <ul className={styles.list}>
            {vibes.map((tag) => (
              <li key={tag.tag_id} className={styles.vibe}>
                <VibeControl
                  {...shared}
                  tag={tag}
                  held={recipeOf(meta, tag.tag_id)}
                  weight={spec.tags.find((weight) => weight.tag_id === tag.tag_id)}
                  problem={why(`tag:${tag.tag_id}`)}
                  scale={scale}
                  crime={countsOf(tag, meta.features)}
                />
                <MadeOf
                  {...shared}
                  tag={tag}
                  features={offered}
                  weights={spec.weights}
                  problemOf={(featureId) => why(`feature:${featureId}`)}
                  open={isOpen(madeOf(tag))}
                  onToggle={(open) => choose(madeOf(tag), open)}
                  // The group says what the scale means once, for every slider it shows.
                  scale={slides ? scale : undefined}
                />
              </li>
            ))}
          </ul>
          {others.length > 0 ? (
            <fieldset className={styles.dimension}>
              <legend className={styles.groupLegend}>
                <span className={styles.tag}>{FEATURES.others}</span>
              </legend>
              <ul className={styles.list}>{controlsOf(others, scale)}</ul>
            </fieldset>
          ) : null}
        </>,
      ),
    );
  }

  // The mix of brands, and every chain a person may ask to be near.
  inside.set("brands", (scale) =>
    sliding(
      scale,
      held.brands.length > 0,
      <>
        <p className={styles.told}>{BRANDS.lead}</p>
        <ul className={styles.list}>{controlsOf(held.brands, scale)}</ul>
      </>,
    ),
  );

  inside.set("apart", (scale) =>
    sliding(scale, held.apart.length > 0, <ul className={styles.list}>{controlsOf(held.apart, scale)}</ul>),
  );

  // Recorded crime is its own group, off until a person switches it on, under its caveat.
  inside.set("crime", (scale) =>
    sliding(
      scale,
      held.crime.length > 0,
      <>
        <p className={styles.told}>{CRIME.lead}</p>
        {/* Where no vibe of the release holds recorded crime, the rule is followed by a line that says so. */}
        {crimeVibes(meta).length === 0 ? <p className={styles.told}>{CRIME_ACCOUNT.noVibe}</p> : null}
        <p className={styles.caveat}>{CRIME_CAVEAT}</p>
        <ul className={styles.list}>{controlsOf(held.crime, scale)}</ul>
      </>,
    ),
  );

  inside.set("hidden", () => (
    <ul className={`${styles.list} ${styles.inside}`}>
      {spec.areas.map((rule) => {
        const name = areas.find((area) => area.area_id === rule.area_id)?.name ?? rule.area_id;
        return (
          <li key={rule.area_id}>
            <Press
              onPress={(event) => {
                // It goes with the press: the focus goes to the one beside it, and from the
                // last of them, whose group goes with it, to the bar of the group before.
                const item = event.currentTarget.closest("li");
                const beside = (item?.nextElementSibling ?? item?.previousElementSibling)?.querySelector("button");
                if (beside) beside.focus({ preventScroll: true });
                else handOn("group", event.currentTarget);
                edit(edits.areaClear(rule.area_id));
              }}
            >
              {rule.rule === "exclude" ? HIDDEN.show(name) : HIDDEN.only(name)}
            </Press>
            {/* It stays while no answer comes, and says why the area is hidden still. */}
            {why(`area:${rule.area_id}`) ? (
              <p className={styles.problem} role="alert">
                {why(`area:${rule.area_id}`)}
              </p>
            ) : null}
          </li>
        );
      })}
    </ul>
  ));

  /** One group: its bar, and under it what it holds while it is open. */
  const bar = ({ key, label, thing, holds }: Group) => (
    <Disclosure
      key={key}
      size="bar"
      label={
        // Its name in the face of names, which is what is read and what names the button.
        <span className={styles.name} data-reads={holdsAFigure(label)}>
          {label}
        </span>
      }
      drawn={<Drawn thing={thing} state="said" />}
      holds={holds}
      open={isOpen(key)}
      onToggle={(open) => choose(key, open)}
      className={styles.group}
    >
      {inside.get(key)?.(`${id}-${key}`)}
    </Disclosure>
  );

  // Their name stands over them where they stand open: before a search, and by the one
  // line that chooses, once one is open too. Behind a button of their own the button names them.
  const titled = standing && (NAMED_IN_SIGHT === "always" || !begun);
  const usual = SAYS_AT_THEIR_HEAD === "what-counts" ? saidOfTheUsual(spec, groups, begun) : null;

  // What the settings hold is the same behind the button and standing open. They stand in
  // one box: their name, and then their groups.
  const all = (
    <>
      {titled ? (
        <h2 id={`${id}-title`} className={styles.title}>
          {SETTINGS.title}
        </h2>
      ) : null}
      {usual === null ? null : <p className={styles.lead}>{usual}</p>}

      {/* Every press and every key is heard here on its way to what it was made on, which
          is the control and takes it: nothing here acts on either. */}
      <div id={`${id}-groups`} className={styles.stack} onPointerDownCapture={inHand.took} onKeyDownCapture={inHand.took}>
        {groups.map(bar)}
      </div>

      {/* One press away the settings stand under the box, a screen and more from Search,
          and this is the button that matters most in sight. Standing open they stand
          beside the box, where Search is in sight: no two cobalt buttons are. */}
      {onRank ? (
        <Press kind={standing ? "plain" : "go"} className={styles.press} onPress={here(onRank)}>
          {SETTINGS.rank}
        </Press>
      ) : null}
    </>
  );

  if (standing) {
    return (
      // The settings themselves are the box, so that a page which stands them on the grass
      // finds a box there and lays no ground of its own under them. They can be given the
      // focus by the page, as when a chip leads to the settings, and are no stop of their own.
      <Frame
        as="section"
        kind="box"
        bare
        className={`${styles.settings} ${styles.standing} ${styles.panel}`}
        // They are found by their name, which is drawn over them or is kept for whoever hears the page.
        {...(titled ? { "aria-labelledby": `${id}-title` } : { "aria-label": SETTINGS.title })}
        aria-busy={busy}
        tabIndex={-1}
      >
        {all}
      </Frame>
    );
  }
  return (
    // The button stands after the first result, which on a phone is the foot of the first
    // screen: what it opens is brought into sight, or nothing is seen to have happened.
    <Disclosure label={SETTINGS.title} open={open} onToggle={onToggle} className={styles.settings} bring>
      {/* What holds the box says how wide it is, so that what is in the box can ask. */}
      <div className={styles.holds}>
        <Frame kind="box" bare className={styles.panel} aria-busy={busy}>
          {all}
        </Frame>
      </div>
    </Disclosure>
  );
}
