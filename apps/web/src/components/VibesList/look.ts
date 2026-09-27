import { BESIDE_A_TRADE_OFF, TRADE_OFF_DRAWN, type BesideATradeOff } from "../ResultList/look";

/**
 * The one line that chooses which two vibes the page names where it says what a vibe is.
 * It is the founder's to overturn.
 *
 * `named`: two vibes of the data, by the names the API gives them, so that the page names
 * no vibe the data does not hold: "such as Leafy or Going out".
 *
 * `written`: the founder's own two, as they wrote them: "such as leafy or well connected".
 * They are written into the website, and are said whatever vibes the data holds.
 */
export type Examples = "named" | "written";

export const EXAMPLES: Examples = "named";

/**
 * Which drawing of a trade-off the key shows, and says what it is: the one a result draws.
 * A result draws a trade-off one of two ways, and no line here chooses between them. The
 * line that chooses how a result draws one chooses for the key as well: `TRADE_OFF_DRAWN`
 * in `ResultList/look.ts`.
 *
 * `scales`: a pair of scales whose pans hang level. `arrows`: two arrows, one each way.
 */
export type TradeOffShown = BesideATradeOff;

export const TRADE_OFF_MAY_BE_SHOWN: readonly TradeOffShown[] = ["scales", "arrows"];

export const TRADE_OFF_SHOWN: TradeOffShown = BESIDE_A_TRADE_OFF[TRADE_OFF_DRAWN];

/**
 * The one line that chooses where the two pictures of every vibe stand on the page of
 * vibes. It is the founder's to overturn.
 *
 * `vibe`: with the vibe, at the ends of the gauge under its map, and nowhere else. The key
 * shows a gauge of two vibes with their pictures, says what the two pictures of a vibe
 * mean, and says that those of each vibe stand with it further down the page. The founder
 * asked for far less in sight on this page, and every pair is on it already.
 *
 * `key`: in the key as well, each pair beside the name of its vibe, under what the two
 * mean. Measured in a browser with the fourteen vibes of the made-up city: the page is
 * then 889 px higher at 390 by 844, and 412 at 1440 by 900.
 */
export type PairsStand = "vibe" | "key";

export const PAIRS_MAY_STAND: readonly PairsStand[] = ["vibe", "key"];

export const PAIRS_STAND: PairsStand = "vibe";
