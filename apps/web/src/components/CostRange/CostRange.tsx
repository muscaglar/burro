import Link from "next/link";

import { ONE_NUMBER } from "@/content/facts";
import { CONFIDENCE, CONFIDENCE_PIPS, COST } from "@/content/search";
import type { Budget, Confidence, CostEstimate, Fact } from "@/lib/api/schema";
import { grouped } from "@/lib/format";
import { paths } from "@/lib/paths";

import { SourceNote } from "../SourceNote/SourceNote";
import styles from "./CostRange.module.css";

/** What a bar is drawn along: the figure at its start and the figure at its end. */
export interface Scale {
  readonly from: number;
  readonly to: number;
}

interface Props {
  /** The `cost` fact: the figures as the API formatted them, with their source and date. */
  readonly fact: Fact;
  /** The same figures as numbers, which place the bar and nothing else. */
  readonly estimate: CostEstimate;
  /** The person's budget, marked on the range where one is set. */
  readonly budget?: Pick<Budget, "amount">;
  /**
   * The scale every bar of a list is drawn on, so that one budget is in one
   * place on all of them and a dearer home is drawn further along. Left out,
   * the bar is drawn on a scale of its own.
   */
  readonly scale?: Scale | null;
}

/** A cost with both its ends. One that lacks either is one number, and no range is drawn for it. */
type Ranged = CostEstimate & { readonly lower_quartile: number; readonly upper_quartile: number };

/** True of a cost that is a range. A publisher's own middle price has no range. */
export function hasARange(estimate: CostEstimate): estimate is Ranged {
  return estimate.lower_quartile !== null && estimate.upper_quartile !== null;
}

/**
 * One scale for several costs and a budget: from a little under the least
 * figure among them to a little over the most. A cost that is one number
 * counts as that number, and nothing stands in for the ends it lacks.
 * `null` when there is no cost to draw.
 */
export function scaleOf(estimates: readonly CostEstimate[], amount: number | null): Scale | null {
  if (estimates.length === 0) return null;
  const figures = [
    ...estimates.flatMap((estimate) =>
      hasARange(estimate) ? [estimate.lower_quartile, estimate.upper_quartile] : [estimate.median],
    ),
    ...(amount === null ? [] : [amount]),
  ];
  const least = Math.min(...figures);
  const most = Math.max(...figures);
  // A little room either side, so that a mark at an end is not cut off.
  const room = Math.max((most - least) * 0.1, 1);
  return { from: least - room, to: most + room };
}

/** Where things sit along the bar, each as a share of its width from 0 to 100. */
export function placesOnBar(estimate: CostEstimate, amount: number | null, scale: Scale | null = null) {
  const { from, to } = scale ?? scaleOf([estimate], amount) ?? { from: 0, to: 1 };
  const width = Math.max(to - from, 1);
  // What a scale does not reach is drawn at its end, and never outside the bar.
  const at = (figure: number) => Math.min(100, Math.max(0, Math.round(((figure - from) / width) * 1000) / 10));
  return {
    // An end the cost does not have is drawn nowhere.
    lower: estimate.lower_quartile === null ? null : at(estimate.lower_quartile),
    median: at(estimate.median),
    upper: estimate.upper_quartile === null ? null : at(estimate.upper_quartile),
    budget: amount === null ? null : at(amount),
  };
}

/** A word for how sure a range is. A price that is one number has none. */
function isConfidence(value: string | undefined): value is Exclude<Confidence, "unstated"> {
  return value === "high" || value === "medium" || value === "low";
}

/**
 * A price that is one number: the middle of what was paid, with no range.
 *
 * It is drawn as one number. No range is made of it. Where it is a publisher's own figure
 * no word says how sure it is, and the line under it says what is not known of it. Where
 * it was counted from sales it says how many, and over which months. The figure, the
 * months, the count and the sentence that says what a middle price means are slots of the
 * fact, as the API formatted them. The bar is drawn only where there is a budget to hold
 * the number against, and says in words where the budget falls.
 */
function OneNumber({ fact, estimate, budget, scale = null }: Props) {
  const { slots } = fact;
  const amount = budget?.amount ?? null;
  const at = placesOnBar(estimate, amount, scale);
  const falls =
    amount === null
      ? null
      : amount < estimate.median
        ? COST.belowMiddle
        : amount > estimate.median
          ? COST.aboveMiddle
          : COST.atMiddle;

  return (
    <div className={styles.cost}>
      <p className={styles.range}>
        <span className={styles.figure}>£{slots.median}</span>
      </p>
      <dl className={styles.facts}>
        <div>
          <dt>{fact.label}</dt>
          <dd>{slots.segment}</dd>
        </div>
        <div>
          <dt>{COST.what}</dt>
          <dd>{COST.middleOfAll}</dd>
        </div>
        {slots.period !== undefined ? (
          <div>
            <dt>{COST.soldIn}</dt>
            <dd>{slots.period}</dd>
          </div>
        ) : null}
        {slots.sales !== undefined ? (
          <div>
            <dt>{COST.sales}</dt>
            <dd>{slots.sales}</dd>
          </div>
        ) : null}
        {amount !== null ? (
          <div>
            <dt>{COST.budget}</dt>
            <dd>£{grouped(amount)}</dd>
          </div>
        ) : null}
      </dl>
      {at.budget !== null ? (
        <div className={styles.bar} role="img" aria-label={COST.pictureOfOne}>
          <span className={styles.median} style={{ insetInlineStart: `${at.median}%` }} />
          <span className={styles.budget} style={{ insetInlineStart: `${at.budget}%` }} />
        </div>
      ) : null}
      {falls !== null ? <p className={styles.falls}>{falls}</p> : null}
      {/* What a middle price means, in the API's words: about half of what sold went for less. */}
      {slots.half_sold ? <p className={styles.falls}>{slots.half_sold}</p> : null}
      {/* A figure that was counted says how many sales it rests on, so nothing is unknown of it. */}
      {slots.sales === undefined ? <p className={styles.falls}>{ONE_NUMBER}</p> : null}
      <SourceNote facts={[fact]} of={fact.label} />
    </div>
  );
}

/**
 * What homes cost in an area: the range, the middle, what it is for, the
 * month it is as of, and how far to trust it.
 *
 * Every figure in words is a slot of the fact, as the API formatted it. The
 * bar is a picture of the same range, and says in words where the budget
 * falls, so it holds nothing the text does not. Confidence is a word; the
 * pips repeat it, and the word leads to what it means.
 */
export function CostRange({ fact, estimate, budget, scale = null }: Props) {
  if (!hasARange(estimate)) return <OneNumber fact={fact} estimate={estimate} budget={budget} scale={scale} />;
  return <Range fact={fact} estimate={estimate} budget={budget} scale={scale} />;
}

function Range({ fact, estimate, budget, scale = null }: Props & { readonly estimate: Ranged }) {
  const { slots } = fact;
  const amount = budget?.amount ?? null;
  const at = placesOnBar(estimate, amount, scale);
  const lower = at.lower ?? at.median;
  const upper = at.upper ?? at.median;
  const rent = fact.template === "cost_rent";
  const confidence = isConfidence(slots.confidence) ? slots.confidence : estimate.confidence;
  const falls =
    amount === null
      ? null
      : amount < estimate.lower_quartile
        ? COST.below
        : amount > estimate.upper_quartile
          ? COST.above
          : COST.inside;

  return (
    <div className={styles.cost}>
      <p className={styles.range}>
        <span className={styles.figure}>
          £{slots.lower} {COST.to} £{slots.upper}
        </span>
        {rent ? ` ${COST.aMonth}` : null}
      </p>
      <dl className={styles.facts}>
        <div>
          <dt>{fact.label}</dt>
          <dd>{slots.segment}</dd>
        </div>
        <div>
          <dt>{COST.middle}</dt>
          <dd>£{slots.median}</dd>
        </div>
        <div>
          <dt>{COST.asOf}</dt>
          <dd>{slots.as_of}</dd>
        </div>
        <div>
          <dt>
            {/* Which page a person reads next is told to no server ahead of time. */}
            <Link className={`${styles.means} target-min`} href={paths.methods("confidence")} prefetch={false}>
              {COST.confidence}
            </Link>
          </dt>
          <dd>
            {CONFIDENCE[confidence]}{" "}
            <span className={styles.pips} aria-hidden="true">
              {[1, 2, 3].map((pip) => (
                <span key={pip} data-on={pip <= CONFIDENCE_PIPS[confidence]} />
              ))}
            </span>
          </dd>
        </div>
        {amount !== null ? (
          <div>
            <dt>{COST.budget}</dt>
            <dd>£{grouped(amount)}</dd>
          </div>
        ) : null}
      </dl>
      <div className={styles.bar} role="img" aria-label={COST.picture}>
        <span
          className={styles.span}
          style={{ insetInlineStart: `${lower}%`, width: `${upper - lower}%` }}
        />
        <span className={styles.median} style={{ insetInlineStart: `${at.median}%` }} />
        {at.budget !== null ? (
          <span className={styles.budget} style={{ insetInlineStart: `${at.budget}%` }} />
        ) : null}
      </div>
      {falls !== null ? <p className={styles.falls}>{falls}</p> : null}
      <SourceNote facts={[fact]} of={fact.label} />
    </div>
  );
}
