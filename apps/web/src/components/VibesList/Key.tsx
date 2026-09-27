import type { CSSProperties } from "react";

import { ABOUT } from "@/content/about";
import { TOWN } from "@/content/town";
import type { MetaData } from "@/lib/api/schema";
import { VIBE_BANDS } from "@/lib/vibes";

import { Part } from "../About/About";
import { KeyGroup, KeyRow } from "../About/KeyRows";
import { Art } from "../kit/Art/Art";
import { faceOf, pictureOf, sizeOf, type Drawing } from "../kit/drawings";
import { STEPS } from "../kit/Gauge/filled";
import { Gauge } from "../kit/Gauge/Gauge";
import { Pennant } from "../kit/Pennant/Pennant";
import type { ThingKind } from "../kit/Thing/drawn";
import { Drawn as DrawnThing, Thing } from "../kit/Thing/Thing";
import { DRAWING_OF_A_TRADE_OFF } from "../ResultList/look";
import { groupsOf, type Group } from "../SettingsPanel/groups";
import { TownKey, TownOfTheKey } from "../Town/TownKey";
import { Track } from "../Track/Track";
import { eachWay } from "../WeightSlider/steps";
import { BandKey } from "./BandKey";
import styles from "./Key.module.css";
import { type PairsStand, TRADE_OFF_SHOWN, type TradeOffShown } from "./look";

interface Props {
  /**
   * The release, from route 11: its vibes, which name themselves and their ends, the
   * measures their recipes are made of, which vibes place any area, the families the
   * vibes are gathered in, and what a search starts from.
   */
  readonly meta: Pick<MetaData, "tags" | "features" | "recipes" | "families" | "defaults">;
  /** Which drawing of a trade-off is shown. Left out, it is what `look.ts` chooses. */
  readonly tradeOff?: TradeOffShown;
  /** Where the two pictures of every vibe stand. Left out, it is what `look.ts` chooses. */
  readonly pairs?: PairsStand;
}

/**
 * The things of a search that are no vibe and that a person meets drawn: a journey, a
 * budget, renting or buying, the kind of home, and an area that was named. The usual
 * settings have no chip, and nothing draws a likeness, so neither is in the key.
 */
export const OTHER_THINGS = ["place", "budget", "tenure", "home", "area"] as const satisfies readonly ThingKind[];

/** The id of each part of the key, which its heading bears and the list at the head of the key leads to. */
export const PARTS = {
  things: "key-things",
  steps: "key-steps",
  result: "key-result",
  map: "key-map",
  town: "key-town",
} as const;

/** The band the steps stand at where the key shows its parts: one that is neither end and not the middle. */
const SHOWN_AT = 4;

/** How much the gauge of the key counts, of a hundred: enough to show a row that is part filled. */
const COUNTS = 60;

/** The pin of the map, as the look draws one. */
const PIN: Drawing = "pin";

/** The groups that are of a person's own choices, each of which the key shows as a thing of a search. */
const SHOWN_AS_THINGS: readonly Group["key"][] = ["money", "journeys", "hidden"];

/**
 * The groups the settings gather what can be asked for in, each with the thing its bar is
 * drawn by: one for each family of vibes, and one for each kind of measurement that is of
 * no family. They are the groups of a search as it starts, so that the key draws what the
 * settings draw and names each as they name it.
 */
function groupsOfThings(meta: Props["meta"]): readonly Group[] {
  return groupsOf(meta.defaults.rent, meta, [], {}).filter((group) => !SHOWN_AS_THINGS.includes(group.key));
}

/** What the style sheet needs of the pin: its picture, its size, and the face it leaves bare for a number, in art pixels. */
function ofThePin(): CSSProperties {
  const { width, height } = sizeOf(PIN);
  const face = faceOf(PIN);
  return {
    "--art": `url("${pictureOf(PIN)}")`,
    "--w": width,
    "--h": height,
    "--left": face.left,
    "--top": face.top,
    "--wide": face.width,
    "--high": face.height,
  } as CSSProperties;
}

/**
 * The key to the drawings: everything a visitor sees drawn anywhere on the website, each
 * at the size it is met, beside what it means in a sentence or two. It stands first on the
 * page of vibes. What a town is built of is a part of it.
 *
 * It holds what is drawn today, and nothing that is gone: the small drawing of every vibe
 * and of every group the things of a search are gathered in, the gauge of a vibe with the
 * one picture of each of its ends, the mark of what is not whole, and what stands beside
 * a trade-off. It says that neither end of a gauge is the better one.
 *
 * It is laid out by where a drawing is met: the things of a search, where an area sits on
 * a vibe, what else stands in a search and on a result, the map, and the town. It opens
 * with those parts by name, each with a drawing or two of what it holds and each a link to
 * its part: the key is long, and a person who has met a drawing finds it by its part,
 * without reading every row.
 *
 * Every drawing is the kit's, or is drawn as the page that shows it draws it, from the
 * same picture and the same tokens. Nothing is drawn that is not in the look already.
 * Nothing of the rabbit is drawn: brown is his alone, and he is no mark to be explained.
 * The drawings are for the eye: what each means is said in words beside it.
 *
 * It is of no area and no search. What it shows of a vibe is by the names the service
 * gives, so no vibe is written into the website. Nothing of it can be pressed but the way
 * to a part of it and the name of a vibe, each of which leads to a place on the same
 * page, and nothing of it moves.
 */
export function Key({ meta, tradeOff = TRADE_OFF_SHOWN, pairs }: Props) {
  const { contents, things, result, map } = ABOUT.key;
  const [first] = meta.tags;
  const groups = groupsOfThings(meta);
  const scale = meta.tags.find((tag) => tag.low_end !== null && tag.high_end !== null);
  /** Each part of the key, in the order they stand: its name, and a drawing or two of what it holds. */
  const parts = [
    {
      id: PARTS.things,
      title: things.title,
      shown: (
        <>
          {first === undefined ? null : <Thing kind="tag" id={first.tag_id} family={first.family} />}
          <Thing kind="place" />
          <Thing kind="budget" />
        </>
      ),
    },
    {
      id: PARTS.steps,
      title: ABOUT.band.title,
      shown: <Track placed={{ band: SHOWN_AT, spread_low: SHOWN_AT, spread_high: SHOWN_AT }} narrow />,
    },
    {
      id: PARTS.result,
      title: result.title,
      // The flag is drawn bare: on a result it bears a rank, which is said in words there and is no part of a name here.
      shown: (
        <>
          <Art name="ui-carrot" alt="" />
          <Art name="ui-flag" alt="" />
          <Art name="ui-key" alt="" />
        </>
      ),
    },
    {
      id: PARTS.map,
      title: map.title,
      shown: (
        <>
          <span className={styles.swatch} data-band={SHOWN_AT} />
          <span className={styles.swatch} data-pattern="unranked" />
          <span className={styles.drawnPin} style={ofThePin()}>
            <span className={styles.drawnFigure}>1</span>
          </span>
        </>
      ),
    },
    { id: PARTS.town, title: TOWN.key.title, shown: <TownOfTheKey meta={meta} /> },
  ] as const;
  return (
    <Part id="key" title={ABOUT.key.title} lay="over" className={styles.key}>
      <div className={styles.groups}>
        <p className={styles.lead}>{ABOUT.key.lead}</p>

        <nav className={styles.toParts} aria-label={contents.label}>
          <p>{contents.lead}</p>
          <ul className={styles.parts}>
            {parts.map(({ id, title, shown }) => (
              <li key={id}>
                <a className="target" href={`#${id}`}>
                  {/* The drawings are dress: the link is named by the name of its part alone. */}
                  <span className={styles.shown} aria-hidden="true">
                    {shown}
                  </span>
                  <span className={styles.named}>{title}</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <KeyGroup id={PARTS.things} title={things.title} className={styles.ofThings}>
          {first === undefined ? null : (
            <KeyRow
              of="vibes"
              size="many"
              drawn={
                <ul className={styles.things} aria-label={things.vibesList}>
                  {meta.tags.map((tag) => (
                    <li key={tag.tag_id}>
                      <a className="target-min" href={`#${tag.tag_id}`}>
                        {/* The drawing is dress: the link is named by the name of the vibe alone. */}
                        <Thing kind="tag" id={tag.tag_id} family={tag.family} />
                        <span>{tag.label}</span>
                      </a>
                    </li>
                  ))}
                </ul>
              }
            >
              <p>{things.vibes}</p>
            </KeyRow>
          )}
          <KeyRow
            of="others"
            size="many"
            drawn={
              <ul className={styles.things} data-things="others" aria-label={things.othersList}>
                {OTHER_THINGS.map((kind) => (
                  <li key={kind}>
                    <span className={styles.thing}>
                      <Thing kind={kind} />
                      <span>{things.kinds[kind]}</span>
                    </span>
                  </li>
                ))}
              </ul>
            }
          >
            <p>{things.others}</p>
          </KeyRow>
          {groups.length === 0 ? null : (
            <KeyRow
              of="groups"
              size="many"
              drawn={
                <ul className={styles.things} data-things="groups" aria-label={things.groupsList}>
                  {groups.map((group) => (
                    <li key={group.key}>
                      <span className={styles.thing}>
                        {/* The drawing is dress: the name beside it is what the group is called. */}
                        <DrawnThing thing={group.thing} state="said" />
                        <span>{group.label}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              }
            >
              <p>{things.groups}</p>
            </KeyRow>
          )}
          {first === undefined ? null : (
            <KeyRow
              of="off"
              size="wide"
              drawn={
                <>
                  <Thing kind="tag" id={first.tag_id} family={first.family} />
                  <Thing kind="tag" id={first.tag_id} family={first.family} state="off" />
                </>
              }
            >
              <p>{things.off}</p>
            </KeyRow>
          )}
          <KeyRow of="gauge" size="wide" drawn={<Gauge counts={COUNTS} steps={STEPS} alone={false} />}>
            <p>{things.gauge}</p>
          </KeyRow>
          {scale === undefined ? null : (
            <KeyRow
              of="gauge-of-a-scale"
              size="wide"
              drawn={
                <Gauge
                  counts={COUNTS}
                  steps={eachWay(STEPS)}
                  ends={[scale.low_end ?? "", scale.high_end ?? ""]}
                  alone={false}
                />
              }
            >
              <p>{things.gaugeOfAScale}</p>
            </KeyRow>
          )}
          <KeyRow of="cross" size="wide" drawn={<Art name="ui-cross" alt="" />}>
            <p>{things.cross}</p>
          </KeyRow>
        </KeyGroup>

        <BandKey meta={meta} id={PARTS.steps} {...(pairs === undefined ? {} : { pairs })} />

        <KeyGroup id={PARTS.result} title={result.title}>
          <KeyRow of="carrot" drawn={<Art name="ui-carrot" alt="" />}>
            <p>{result.carrot}</p>
          </KeyRow>
          <KeyRow
            of="rank"
            drawn={
              // On a result the pennant says its rank to whoever hears the page. Here it is of
              // no result: it is drawn for the eye, and what it means is said beside it.
              <span aria-hidden="true">
                <Pennant rank={1} />
              </span>
            }
          >
            <p>{result.rank}</p>
          </KeyRow>
          <KeyRow of="source" drawn={<Art name="ui-key" alt="" />}>
            <p>{result.source}</p>
          </KeyRow>
          <KeyRow of="trade-off" drawn={<Art name={DRAWING_OF_A_TRADE_OFF[tradeOff]} alt="" />}>
            <p>{result.tradeOff[tradeOff]}</p>
          </KeyRow>
          <KeyRow of="arrow" drawn={<Art name="ui-arrow" alt="" />}>
            <p>{result.arrow}</p>
          </KeyRow>
          <KeyRow of="notice" drawn={<span className={styles.noteEdge} data-edge="notice" aria-hidden="true" />}>
            <p>{result.notice}</p>
            <p>{result.never}</p>
          </KeyRow>
          <KeyRow of="fault" drawn={<span className={styles.noteEdge} data-edge="fault" aria-hidden="true" />}>
            <p>{result.fault}</p>
          </KeyRow>
        </KeyGroup>

        <KeyGroup id={PARTS.map} title={map.title}>
          <KeyRow
            of="greens"
            size="many"
            drawn={
              // The five are drawn for the eye. What they are is said beside them.
              <span className={styles.shades} aria-hidden="true">
                {VIBE_BANDS.map((band) => (
                  <span key={band} className={styles.swatch} data-band={band} />
                ))}
              </span>
            }
          >
            <p>{map.greens}</p>
          </KeyRow>
          <KeyRow of="sand" drawn={<span className={styles.swatch} data-band={0} aria-hidden="true" />}>
            <p>{map.sand}</p>
          </KeyRow>
          <KeyRow of="dots" drawn={<span className={styles.swatch} data-pattern="unranked" aria-hidden="true" />}>
            <p>{map.dots}</p>
          </KeyRow>
          <KeyRow of="lines" drawn={<span className={styles.swatch} data-pattern="filtered" aria-hidden="true" />}>
            <p>{map.lines}</p>
          </KeyRow>
          <KeyRow of="water" drawn={<span className={styles.swatch} data-water aria-hidden="true" />}>
            <p>{map.water}</p>
          </KeyRow>
          <KeyRow
            of="pin"
            drawn={
              <span className={styles.drawnPin} style={ofThePin()} aria-hidden="true">
                <span className={styles.drawnFigure}>1</span>
              </span>
            }
          >
            <p>{map.pin}</p>
          </KeyRow>
        </KeyGroup>

        <TownKey meta={meta} id={PARTS.town} />
      </div>
    </Part>
  );
}
