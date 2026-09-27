"use client";

import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type MouseEvent,
  type ReactNode,
  type SyntheticEvent,
} from "react";

import { HELPERS, type HelperId } from "@/content/helpers";
import { MAP } from "@/content/map";
import { FIND_AREA, leadFor, NOTICE, PLACE, PROMPT, REJECTED_PART, RESULTS, SEARCH, SUGGEST } from "@/content/search";
import { SETTINGS } from "@/content/settings";
import { SHARED } from "@/content/share";
import { DEEP, REFINE, UNREAD, WAY_IDS, WAYS, type WayId } from "@/content/ways";
import type { Client } from "@/lib/api/client";
import type { Handed } from "@/lib/api/handed";
import type { AreaSummary, Span, TagId, VibeBands } from "@/lib/api/schema";
import { examplesFor, isPlaced, placedOf } from "@/lib/holds";
import { startsFrom } from "@/lib/search/begins";
import { isEmpty, partsOf } from "@/lib/search/edits";
import type { How } from "@/lib/search/flow";
import { isSaidAsMissing, missingFrom, refusals, refusedByPart } from "@/lib/search/refusals";
import { isStale, repairsFor } from "@/lib/search/repairs";
import { noticeOf, leftOutOf, refusedOf } from "@/lib/search/said";
import { inTheBox } from "@/lib/search/spans";
import {
  failureOfTheCards,
  changedTheSearch,
  isUnreachable,
  nothingCameOf,
  profilesFailed,
  reasonsAreIn,
  reasonsFailure,
  servedTheRanking,
  type SearchState,
} from "@/lib/search/state";
import { SearchProvider, useSearch } from "@/lib/search/store";
import { SessionBoundary, useMadeLink, useSessionIfAny } from "@/lib/session/session";
import { bringWholeIntoSight, DOUBLE_PRESS_MS } from "@/lib/sight";
import type { Lens } from "@/lib/vibes";

import { AreaTable } from "../AreaTable/AreaTable";
import { ChipRow } from "../ChipRow/ChipRow";
import { CompareTray } from "../CompareTray/CompareTray";
import { Invite, invites } from "../CompareTray/Invite";
import { Disclosure } from "../Disclosure/Disclosure";
import { ErrorBlock } from "../ErrorBlock/ErrorBlock";
import { Helpers, type Helper } from "../Helpers/Helpers";
import { KeepSearch } from "../KeepSearch/KeepSearch";
import { Burro } from "../kit/Burro/Burro";
import { Frame } from "../kit/Frame/Frame";
import { Press } from "../kit/Press/Press";
import { MapView } from "../MapView/MapView";
import { NothingMatches } from "../NothingMatches/NothingMatches";
import { NotInData } from "../NotInData/NotInData";
import {
  NoticeBlock,
  OfflineLine,
  RejectedList,
  StateLine,
  UnmetList,
} from "../NoticeBlock/NoticeBlock";
import { PlaceCombobox } from "../PlaceCombobox/PlaceCombobox";
import { Examples, PromptBox, type PromptHandle } from "../PromptBox/PromptBox";
import { OVER_THE_LIST, type OverTheList } from "../ResultList/look";
import { ResultList, type Part } from "../ResultList/ResultList";
import { SettingsPanel } from "../SettingsPanel/SettingsPanel";
import { SharedHeader } from "../SharedSearch/SharedHeader";
import { SharePanel } from "../SharePanel/SharePanel";
import { Shelf } from "../Shelf/Shelf";
import { StatusLine } from "../StatusLine/StatusLine";
import { Small } from "../Suggestions/Small";
import {
  AN_AREA_BY_NAME,
  DEEP_SEARCH_RANKS_BY,
  ON_A_NARROW_SCREEN,
  OVER_THE_ANSWER_GIVES_WAY,
  THE_BUTTON_OF_DEEP_SEARCH,
  type ButtonStands,
  type FindsAnArea,
  type GivesWay,
  type Ranks,
  type Stands,
} from "./look";
import { orderOf, type Part as PartOfThePage } from "./order";
import { tellHowHigh } from "./bar";
import { LeftOut } from "./LeftOut";
import { useFocusKept, useScreen } from "./screen";
import styles from "./SearchApp.module.css";
import { Wait, type Room } from "./Wait";
import { panelOf, tabIdOf, Ways } from "./Ways";

interface Props {
  /** What a form needs: the vocabulary, both defaults and the limits. From route 11, at build. */
  readonly meta: Handed;
  /** Every area of the release, from route 4, at build. */
  readonly areas: readonly AreaSummary[];
  /**
   * Where every area sits on every vibe that some area is placed on, from route 4, at build.
   * They come with the page, so that nobody is told which vibe a person looks at. The map
   * is coloured by them before a search, and the town of each result is drawn from them.
   */
  readonly bands?: readonly VibeBands[];
  /** The API to call. A test passes its own. */
  readonly client?: Client;
  /** What becomes of the page as a search opens of a setting that was moved. Left out, as the look has chosen. */
  readonly opens?: Opens;
  /** Where the part that refines a search stands on a narrow screen. Left out, as the look has chosen. */
  readonly refines?: Stands;
  /** When what stands over the answer gives way further. Left out, as the look has chosen. */
  readonly gives?: GivesWay;
  /** What stands over the list of results. Left out, as the look has chosen. */
  readonly over?: OverTheList;
  /** What makes a search of the second way in, before a search. Left out, as the look has chosen. */
  readonly ranks?: Ranks;
  /** Where an area is found by its name. Left out, as the look has chosen. */
  readonly finds?: FindsAnArea;
  /** Where the button that makes a search of the second way in stands. Left out, as the look has chosen. */
  readonly button?: ButtonStands;
}

/**
 * What becomes of the page as a search opens of a setting that was moved, in the second
 * of the two ways in, where the look has a setting make the search and not the button of
 * the way. The settings stay open, as the part that refines the search, and the answer is
 * drawn about them. Two promises meet there and both cannot be kept, so it is the
 * founder's to choose.
 *
 * `held`: the setting stays where it stood in the window, so that a press lands where it
 * was aimed, and the answer is drawn over it and under it, out of sight, as it is whenever
 * a setting is moved with a search open. `answer`: the box is brought into sight with the
 * answer under it, as it is for a word of the shelf, so that the first result is in sight
 * once a ranking follows the press. The setting keeps the focus and goes from under the
 * hand, and a press the browser counts as the second of a double press lands on nothing.
 */
export type Opens = "held" | "answer";

export const OPENS: readonly Opens[] = ["held", "answer"];

/** What becomes of it where the page does not say. This one line chooses. */
const A_SETTING_OPENS: Opens = "held";

/** What can be pressed or typed in: what a press in the settings was made on. */
const CONTROL = "button, input, select, textarea, a, label";

const PANEL = { list: "results", map: "panel-map" } as const;
/** What opens and closes the part that refines a search: the button of a fold. */
const OPENS_IT = "button[aria-expanded][aria-controls]";
/**
 * What Burro's box holds the room of while a first search is read, which is the founder's
 * to choose. `result`: the first result, so that he hops where the results will stand.
 * `answer`: what Burro understood and the first result under it, so that the first result
 * ends where he hopped.
 */
const ROOM: Room = "answer";
/** The chips, which the page gives the focus to when a question is answered and goes. */
const UNDERSTOOD = "understood";

/** Where the field of the form stands in the window, or `null` where there is none, or no browser lays it out. */
function fieldOf(form: HTMLElement | null): number | null {
  return form?.querySelector("textarea")?.getBoundingClientRect().top ?? null;
}

/** For how long the field is held where it stood, while what came back over it settles. */
const SETTLES_MS = 1500;

/** What a person does that moves the page, or that is aimed at it as it stands: from then nothing holds it. */
const TAKES_THE_PAGE = ["wheel", "touchmove", "pointerdown", "keydown"] as const;

/**
 * Holds the field so far down the window while the parts of the page settle about it, and
 * answers with what lets go of it. A part that is drawn again at another size may take
 * its size a moment late, as a map does: measured on a phone, the map that came back over
 * the box was 392 px high as the page was laid out and 210 once it had settled, and the
 * field went 182 px up the window after the page had been moved to hold it. It is held as
 * each part takes its size, before the page is drawn, for a moment and no longer, and is
 * let go of as soon as a person moves the page or presses anything. A browser that says
 * nothing of sizes holds nothing.
 */
function settledAt(
  at: number,
  parts: HTMLElement | null,
  form: HTMLElement | null,
  ours: { current: number | null },
): (() => void) | null {
  if (typeof ResizeObserver !== "function" || parts === null) return null;
  const watched = new ResizeObserver(() => {
    const now = fieldOf(form);
    if (now === null || Math.abs(now - at) < 1) return;
    window.scrollBy(0, now - at);
    ours.current = window.scrollY;
  });
  const letGo = () => {
    watched.disconnect();
    window.clearTimeout(timer);
    for (const name of TAKES_THE_PAGE) window.removeEventListener(name, letGo, true);
  };
  const timer = window.setTimeout(letGo, SETTLES_MS);
  for (const name of TAKES_THE_PAGE) window.addEventListener(name, letGo, { capture: true, passive: true });
  watched.observe(parts);
  return letGo;
}

/** What a failure is shown as. One failure is shown in one place. */
function placeOf(state: SearchState): "none" | "offline" | "box" | "form" | "block" {
  const { failure, failedStep } = state;
  if (failure === null) return state.online ? "none" : "offline";
  if (failure.kind === "offline") return "offline";
  if (failure.kind === "api" && failure.code === "invalid_text") return "box";
  // A request the API refused, other than for its words, is a fault to report and is said
  // in the API's own words. Left to the form it would be said nowhere: the form speaks
  // only when the words went unread.
  const refused = failure.kind === "api" && failure.status < 500;
  // Words that could not be read are not a fault to report. The form does the same job.
  // Words that never reached Burro are another thing: the form could not reach it either,
  // so the page says that Burro could not be reached, as it does for a control.
  if (failedStep === "read" && !isStale(failure) && !refused && !isUnreachable(failure)) return "form";
  return "block";
}

/**
 * The search page: one box to type in, what Burro understood, and the answer.
 *
 * Typing and the controls both end in edits the API applies. Nothing a
 * person types is kept here: the sentence goes from its box to one call.
 */
export function SearchApp({ meta, areas, bands = [], client, opens, refines, gives, over, ranks, finds, button }: Props) {
  return (
    // The search is kept by the session, so that it is still there when the person comes back.
    <SessionBoundary>
      <SearchProvider meta={meta} areas={areas} client={client}>
        <SearchView
          bands={bands}
          opens={opens}
          refines={refines}
          gives={gives}
          over={over}
          ranks={ranks}
          finds={finds}
          button={button}
        />
      </SearchProvider>
    </SessionBoundary>
  );
}

interface ViewProps {
  /** True on the page a shared link opens, whose heading says that the search is a shared one, to whoever hears the page. */
  readonly shared?: boolean;
  /** Where every area sits, as the page that holds the search was built with it. */
  readonly bands?: readonly VibeBands[];
  /** What becomes of the page as a search opens of a setting that was moved. Left out, as the look has chosen. */
  readonly opens?: Opens;
  /** Where the part that refines a search stands on a narrow screen. Left out, as the look has chosen. */
  readonly refines?: Stands;
  /** When what stands over the answer gives way further. Left out, as the look has chosen. */
  readonly gives?: GivesWay;
  /** What stands over the list of results. Left out, as the look has chosen. */
  readonly over?: OverTheList;
  /** What makes a search of the second way in, before a search. Left out, as the look has chosen. */
  readonly ranks?: Ranks;
  /** Where an area is found by its name. Left out, as the look has chosen. */
  readonly finds?: FindsAnArea;
  /** Where the button that makes a search of the second way in stands. Left out, as the look has chosen. */
  readonly button?: ButtonStands;
}

/** Where a part of the page stood in the window as a press was made. */
interface Stood {
  readonly part: HTMLElement;
  readonly top: number;
}

/** Which stretch of what was not read is selected in the box: which one, of how many. */
interface Shown {
  readonly at: number;
  readonly among: number;
}

/**
 * The search page itself, for whatever holds the search: the page at `/`, or an opened share.
 *
 * Before a search it says who it is for, and offers two ways in, as two
 * tabs, with the map in sight whichever is chosen: beside them on a wide
 * screen, and over them, low, where the page is one column. "Quick search" is chosen
 * at first: the box, and under it two helpers, each closed until it is
 * pressed, the examples and the shelf of vibes. "Deep search" holds a
 * sentence that says what it is, the settings, which stand open with their
 * first two groups open, and the button that ranks by them, which is held at
 * the foot of the window for as long as its own place is under it: it stood
 * under ten groups, and a person who had chosen did not find it. It asks
 * nothing of its own: the settings are its questions. Nothing is lost by
 * changing tab: both panels are on the page, and the one that is not chosen
 * is not drawn. The second is drawn for the first time when it is first chosen.
 *
 * The second way is built by choosing and then searching. What is chosen in
 * its settings is kept, and no search is made of it: the tabs stay, and
 * nothing is ranked for the page, until the button that ranks by the
 * settings is pressed. One line of the look has the first setting that is
 * moved make the search, as it did.
 *
 * The tabs are for beginning. Once a search is open the two ways have become
 * one search: the box on one line at the head of the page, one line that
 * says what happened, the chips, and then the settings as one part that is
 * closed until it is pressed, "Refine search", and the results. The title
 * gives way to the answer. "Start again" brings the two tabs back.
 *
 * The answer comes first. On a narrow screen the first result is whole on
 * the first screen, and the part that refines stands directly after it, in
 * the page as on the screen. After the first result stand the way to
 * sharing, the map, and the rest of the results: from 60rem the map is beside
 * them all, and stays in sight as they scroll. Everything else is one press
 * away: the working of a result, the settings, sharing, the table.
 *
 * The order of the page is the order it is drawn in, on every screen: no
 * rule of the style sheet draws a part out of its place. The sheet says which
 * screen there is, in one word, and the page puts its parts in the order that
 * screen draws them in. A part that changes its place is the part it was.
 *
 * An area that is chosen on the map opens its card by the map, and the page
 * stays where it is. The list is told of it when the card is asked to show
 * it in the list, and brings it into sight then.
 *
 * On a wide screen the first result is in sight without scrolling, and what
 * stands over it is, in this order and no more: the box, with what Burro says
 * of the search and what he understood in it, what he did not read, and one
 * line that holds what refines the search and, beside it, what says that
 * areas can be compared. Nothing stands between that line and the first
 * result.
 *
 * The settings that stand in the second way and the settings that refine a
 * search are one part in one place of the page. So where the look has a
 * search open of a setting that was moved, the settings are as they were,
 * open, with what was moved in hand.
 *
 * What Burro says of a search stands directly under the box: what happened, a
 * notice, a failure, what was understood, and what was not read or not
 * taken. It is what a person must see when they press Search.
 *
 * The page asks nothing. What Burro noticed in a sentence it takes of itself,
 * as soon as the reading is in, and ranks: everything it took is a chip of
 * what it understood, which can be taken off, and what nobody said in so
 * many words says that it was assumed. What it took nothing of is said in a
 * line, with why. No dialogue stands between a press and the answer.
 *
 * The page stands on the meadow, and every part of it in a box of its own
 * with grass between: the heading with Burro sitting beside it, the box with
 * what Burro says of the search in it, what he noticed, each result, the
 * settings, the map. Nothing is read on the grass. A part that another
 * component draws, and that brings no box, is given a slip of cream by the
 * page: the style sheet says how.
 *
 * While a sentence is read Burro hops where the results will stand, in a box
 * of the size of the result that stood there. The results stand where he was
 * when the answer is in. He hops there too while a first ranking that a
 * control asked for is worked out, and the search is open from that press as
 * it is from the press that sends a sentence. He does not hop while a ranking
 * is worked out again: the list stays in sight, and says so.
 *
 * A search that begins with no results in sight is answered no sooner than he
 * has been seen to go down his hole and come up again: the search itself
 * holds its answer so long, and the page draws what the search holds. Until
 * then he has the stage, and what was understood comes with the answer.
 */
export function SearchView({
  shared = false,
  bands = [],
  opens = A_SETTING_OPENS,
  refines = ON_A_NARROW_SCREEN,
  gives = OVER_THE_ANSWER_GIVES_WAY,
  over = OVER_THE_LIST,
  ranks = DEEP_SEARCH_RANKS_BY,
  finds = AN_AREA_BY_NAME,
  button = THE_BUTTON_OF_DEEP_SEARCH,
}: ViewProps) {
  const { state, flow } = useSearch();
  const [madeLink, keepLink] = useMadeLink();
  const id = useId();
  const prompt = useRef<PromptHandle>(null);
  // The page itself, of which the style sheet says which screen there is.
  const page = useRef<HTMLDivElement>(null);
  const screen = useScreen(page);
  // What holds the form, the map and both parts of the list of results.
  const columns = useRef<HTMLDivElement>(null);
  const form = useRef<HTMLElement>(null);
  const map = useRef<HTMLDivElement>(null);
  // Where the settings stand: in the second of the two ways in, and then in the part that refines a search.
  const refine = useRef<HTMLDivElement>(null);
  // Where the results stand, and where Burro hops until the first of them is in.
  const results = useRef<HTMLElement>(null);
  // What stands in the place of the first result: the first result, or what says that no area passes.
  const first = useRef<HTMLDivElement>(null);
  // Which of the two ways in is chosen, before a search. The first, until the other is pressed.
  const [way, setWay] = useState<WayId>("quick");
  // True once the second way has been chosen: it is drawn for the first time then, and kept.
  const [deep, setDeep] = useState(false);
  const [reveal, setReveal] = useState<{ areaId: string; at: number } | null>(null);
  // The area that was chosen on the map itself, by its pin or by its ground, until it is
  // shown in the list or another is chosen. The list is not told of it: told, it brought
  // the result of that area into sight, and the page went from under the pin that was
  // pressed. Seen on a phone: by 411 px, with the card of the map left under the window.
  const [onTheMap, setOnTheMap] = useState<string | null>(null);
  // Which stretch of what was not read is selected in the box. Where words stand is known
  // for the text that was sent, and for no other, so this goes when the box changes.
  const [shown, setShown] = useState<Shown | null>(null);
  // The vibe the map is coloured by, before a search. It is the one whose card is open.
  const [looksAt, setLooksAt] = useState<TagId | null>(null);
  // The helper the person opened, before a search. Every one is closed until it is pressed.
  const [helper, setHelper] = useState<HelperId | null>(null);
  // How high what stood in the place of the first result was when a sentence was last sent.
  // Burro hops in a box of that size, so that nothing under him moves when he comes.
  const [room, setRoom] = useState<number | null>(null);
  // Set when what was pressed stood under the box and a search opens of it. What goes as the
  // search opens, a vibe on the shelf or the place field, hands the focus to what Burro
  // understood. The button that ranks the settings goes too, and hands it to what opens
  // them. The settings stay, and keep it. Either way the answer is brought into sight.
  const handsOver = useRef<"understood" | "sight" | "answer" | null>(null);
  // Where the field stood in the window as the sentence that opens a search was sent.
  const stood = useRef<number | null>(null);
  // Where the field is to stand if that search closes again with nothing to show, as where
  // Burro cannot be reached: where it stood as the sentence was sent, until a person moves
  // the page or presses something while they wait, and from then where that left it.
  const sentFrom = useRef<number | null>(null);
  // How far down the page stood once the page itself last moved it: what the page did is
  // not taken for what a person did.
  const ours = useRef<number | null>(null);
  // Whether a search was open as the page was last laid out.
  const laidOpen = useRef(false);
  // What lets go of the field, while it is held until the page has settled about it.
  const settle = useRef<(() => void) | null>(null);
  // What a press in the second way was made on, and where it stood in the window, while no
  // search is open: what was pressed, and what had the focus, which is what is left where
  // what was pressed goes with the press.
  const hand = useRef<readonly Stood[] | null>(null);
  // When the page was last moved from under a press, by the clock of the page.
  const moved = useRef<number | null>(null);
  // What is to take the focus once the page is next drawn, where what it is put on may not
  // be drawn yet: Search, and the box, stand in the first way in, which is not drawn while
  // the second is chosen.
  const then = useRef<(() => void) | null>(null);
  // True while the focus is where the page put it as a search opened of the button that
  // ranks the settings: on what opens them. It goes with the search if its ranking does not come.
  const atWhatRefines = useRef(false);
  // The button that makes a search of the second way in, where it is held in sight.
  const held = useRef<HTMLButtonElement>(null);
  // Each is for the search that opens of that press, and for no other. A press may open none:
  // the settings may be ranked while a search is open, and Burro may not be reached. So a
  // press is forgotten as the next one begins, and the page is never moved for one made
  // before, as it was for a sentence typed after such a press, in the box where the person was.
  const forget = () => {
    handsOver.current = null;
    stood.current = null;
    hand.current = null;
    atWhatRefines.current = false;
  };
  /** Where the field stands in the window, or `null` where no browser lays it out. */
  const fieldStands = () => fieldOf(form.current);
  const session = useSessionIfAny();

  // What another page asked the search to add, as "Search for this character" does on the
  // page of an area. It is taken once, and sent as the edits of a control are.
  useEffect(() => {
    const wanted = session?.wanted.take() ?? null;
    if (wanted === null || isEmpty(wanted)) return;
    handsOver.current = "understood";
    void flow.applyEdits(wanted);
  }, [session, flow]);

  useEffect(() => {
    void flow.loadGeometry();
    // Who reads what is typed is asked of the service as the page opens, and not taken
    // from what the page was built on: no sentence is sent until the service has said, so
    // it is asked before one is typed.
    void flow.loadReader();
    if (typeof navigator !== "undefined" && navigator.onLine === false) flow.wentOffline();
    const online = () => void flow.wentOnline();
    const offline = () => flow.wentOffline();
    window.addEventListener("online", online);
    window.addEventListener("offline", offline);
    return () => {
      window.removeEventListener("online", online);
      window.removeEventListener("offline", offline);
    };
  }, [flow]);

  // "Show in the list": the card is brought into view and takes the focus. It is brought in
  // by its top, so that its heading is in sight.
  useEffect(() => {
    if (reveal === null) return;
    // A pin of the map names its area as a result does. The result is the one that holds a card.
    const card = [...(columns.current?.querySelectorAll<HTMLElement>("li[data-area]") ?? [])]
      .find((item) => item.dataset.area === reveal.areaId)
      ?.querySelector<HTMLElement>("article");
    if (!card) return;
    if (typeof card.scrollIntoView === "function") card.scrollIntoView({ block: "start" });
    card.focus({ preventScroll: true });
  }, [reveal]);

  const { spec, meta, areas, ranking, read, phase } = state;
  const reading = phase === "interpreting";
  const busy = reading || phase === "refining";
  // A control asked for a first ranking, and it is on its way: the settings ranked as they
  // stand, a word of the shelf, a place, a setting that was moved, a thing Burro offered.
  // A person waits there for a first answer, as they do while a first sentence is read.
  const asked = phase === "refining" && ranking === null;
  // A search is open once anything has been read, ranked or changed, and while a person
  // waits for a first answer: from the press that sends a sentence, and from the press that
  // asks for a first ranking. A ranking that does not come leaves the page as it was. What
  // the second way in has gathered changed the spec and made no search: none is open of it.
  const open = reading || asked || read !== null || ranking !== null || (!state.untouched && !state.gathering);
  // What is made of what is chosen in the settings. Before a search the second way in
  // gathers it, where the look has its button make the search.
  const how: How = !open && ranks === "button" ? "gather" : "rank";
  const shows = placeOf(state);

  // While the button of the second way in is held in sight, the style sheet is told how
  // high its bar is: what takes the focus among the space requirements is brought clear
  // of the bar by as much, whatever Burro says in it.
  const barIsDrawn = !open && deep && button === "held";
  useEffect(() => {
    const bar = barIsDrawn ? (held.current?.parentElement ?? null) : null;
    return bar === null ? undefined : tellHowHigh(bar);
  }, [barIsDrawn]);

  // The two ways in and what they hold are for a first search, and go when one opens. The
  // focus goes to what Burro understood, which is where what was pressed has gone. It is
  // never left on nothing.
  useEffect(() => {
    if (!open || handsOver.current === null) return;
    const to = handsOver.current;
    // What brings the first result into sight waits for the ranking, which is on its way.
    if (to !== "sight") handsOver.current = null;
    if (to === "understood") document.getElementById(UNDERSTOOD)?.focus({ preventScroll: true });
    // The button that ranked the settings went as it was pressed, and the settings are
    // closed over the answer: what opens them is where they now are.
    if (to === "sight") {
      const opens = refine.current?.querySelector<HTMLElement>(`:scope > * > ${OPENS_IT}`);
      // It was not drawn while the settings stood open, and is from now.
      if (opens) opens.hidden = false;
      opens?.focus({ preventScroll: true });
      atWhatRefines.current = true;
    }
    // What was pressed stays, and has gone from under the pointer with the page.
    if (to === "answer") moved.current = performance.now();
    // The page may stand where it was scrolled to for what was pressed, which a browser
    // brings clear of the foot of the screen as it takes the focus. The answer begins at the
    // box, some way above: a word added from the shelf left the first result out of sight,
    // over the top of the screen. So the box is brought into sight, where it is not, with
    // what Burro understood and the first result under it.
    if (typeof form.current?.scrollIntoView === "function") form.current.scrollIntoView({ block: "nearest" });
  }, [open]);

  // A search that opened of a press closes again where its ranking does not come, and what
  // the page gave the focus to as it opened goes with it: what opens the settings, what
  // Burro understood, or Search, which is not drawn while the second way in is chosen. The
  // focus goes to the tab of the way the person is in, over which the failure is said. It
  // is never left on nothing. Where the focus is on what is drawn still, it stays, and where
  // something is to take it once the page is drawn, as the box is where a search begins
  // again, that takes it.
  const wasOpen = useRef(open);
  useEffect(() => {
    const closed = wasOpen.current && !open;
    wasOpen.current = open;
    if (!closed) return;
    const on = document.activeElement;
    const gone =
      atWhatRefines.current || !(on instanceof HTMLElement) || on === document.body || on.closest("[hidden]") !== null;
    // The button that was pressed is drawn again where it stood, where it is held in sight:
    // it is what the focus was on, and has it again.
    const pressed = atWhatRefines.current ? held.current : null;
    atWhatRefines.current = false;
    if (!gone || then.current !== null) return;
    (pressed ?? document.getElementById(tabIdOf(id, way)))?.focus({ preventScroll: true });
  }, [open, id, way]);

  // What was to take the focus once the page was drawn takes it.
  useEffect(() => {
    const to = then.current;
    then.current = null;
    to?.();
  });

  // Before a search the settings stand open in the second way in, and nothing opens or
  // closes them: what would is not drawn. The style sheet says so, and the page says it of
  // the button too, so that it is no stop of a keyboard and is not heard, whatever draws
  // the page. It is the fold's own button, and the fold does not say whether it is hidden.
  useLayoutEffect(() => {
    const opens = refine.current?.querySelector<HTMLElement>(`:scope > * > ${OPENS_IT}`);
    if (opens) opens.hidden = !open;
  });

  // The settings may be ranked as they stand while a search is open and nothing is ranked,
  // as where nothing of a sentence was read. No search opens of that press, and what Burro
  // says of the search stands between the box and the first result. So once the ranking of
  // that press is in, the first result is brought into sight, as far as it must be.
  useEffect(() => {
    if (ranking === null || handsOver.current !== "sight") return;
    handsOver.current = null;
    if (typeof first.current?.scrollIntoView === "function") first.current.scrollIntoView({ block: "nearest" });
  }, [ranking]);

  // While that ranking is on its way Burro hops where the results will stand. What a press
  // asked for is seen: where the results will stand is brought into sight as the press
  // lands, as far as it must be, and the first result then stands where he hopped.
  useEffect(() => {
    if (!asked || handsOver.current !== "sight") return;
    if (typeof results.current?.scrollIntoView === "function") results.current.scrollIntoView({ block: "nearest" });
  }, [asked]);

  // A search opens of a setting that was moved, in the second of the two ways in. The
  // heading and the tabs over the settings go and the answer is drawn about them, and they
  // go up or down the page by as much: seen on a phone, the plus of a slider went from 501
  // of 844 to 23, and the way to another group of settings stood where it had been. So the
  // page goes by as much as the setting went, before anything is drawn: as the search
  // opens, as its first ranking comes, and as it closes again where the ranking does not
  // come. With a search open a browser holds the page itself, and nothing is asked of it here.
  useLayoutEffect(() => {
    const held = hand.current;
    if (held === null) return;
    // While the ranking is on its way it may yet move what stands over the settings. A press
    // that hands the focus on, or brings the answer into sight, keeps nothing under the hand.
    if (!asked || handsOver.current !== null) hand.current = null;
    if (handsOver.current !== null) return;
    const still = held.find(({ part }) => part.isConnected);
    if (still === undefined) return;
    const now = still.part.getBoundingClientRect().top;
    if (now !== still.top) window.scrollBy(0, now - still.top);
  }, [open, asked, ranking]);

  // The ranking may be slow, and a person may scroll the page meanwhile. The page goes
  // where they take it: the setting is held where that leaves it, and they are not brought
  // back to where it stood when the ranking comes.
  useEffect(() => {
    const scrolled = () => {
      // So it is with the field, while a first search waits for its answer.
      if (sentFrom.current !== null && window.scrollY !== ours.current) sentFrom.current = fieldOf(form.current);
      if (hand.current === null) return;
      hand.current = hand.current.map(({ part }) => ({ part, top: part.getBoundingClientRect().top }));
    };
    window.addEventListener("scroll", scrolled, { passive: true });
    return () => window.removeEventListener("scroll", scrolled);
  }, []);

  // As a first search opens the heading over the box gives way to the answer, and all that
  // stands under it goes up by as much. Where the page had been scrolled, the box went up and
  // out of the window from under the press that sent the sentence, and the first result went
  // after it. So the page goes back by as much as went from over the field, before anything
  // is drawn. A browser stops at the top of the page: from there the box goes up to where
  // the heading was, as it did.
  //
  // A search that opened of a sentence closes again where nothing came of it: Burro could
  // not be reached, or the person stopped it. The heading comes back over the box, and the
  // box went down the window by as much: seen on a phone, 398 px, from under the press. So
  // the page goes on by as much as came back over the field. To begin again is to come
  // back to the first page, and nothing is held for it.
  //
  // What says that a first search failed stands in the box, directly under the field, and
  // the whole of it is brought into sight, as far as it must be: seen on a phone, a person
  // pressed Search and saw the page as it had been, with what said that Burro could not be
  // reached under the foot of the window. The press has landed by then. With results in
  // sight nothing is moved: a person may be anywhere among them when an answer does not come.
  const failed = state.failure;
  const saidOf = useRef<typeof failed>(null);
  useLayoutEffect(() => {
    const opened = open && !laidOpen.current;
    const closed = !open && laidOpen.current;
    laidOpen.current = open;
    const was = opened ? stood.current : closed ? sentFrom.current : null;
    stood.current = null;
    if (closed) sentFrom.current = null;
    const field = form.current?.querySelector("textarea") ?? null;
    const now = field?.getBoundingClientRect().top ?? null;
    if (was !== null && now !== null && now !== was) {
      window.scrollBy(0, now - was);
      ours.current = window.scrollY;
    }
    // A failure is said once, as it comes: what is drawn again is not brought up again.
    const isNew = failed !== saidOf.current;
    saidOf.current = failed;
    const said = isNew && failed !== null && ranking === null ? form.current?.querySelector<HTMLElement>("[data-failure]") : null;
    const by = said ? bringWholeIntoSight(said, field) : 0;
    if (by > 0) {
      ours.current = window.scrollY;
      // What was pressed has gone from under the pointer by as much.
      moved.current = performance.now();
    }
    // What came back over the field may settle late, as a map does that is drawn smaller:
    // the field is held where it now stands until the page has settled about it.
    if (closed && was !== null) {
      settle.current?.();
      settle.current = settledAt(was - by, columns.current, form.current, ours);
    }
  }, [open, failed, ranking]);

  // Once a search has something to show it does not close again, and nothing is held for it.
  useEffect(() => {
    if (read !== null || ranking !== null) sentFrom.current = null;
  }, [read, ranking]);

  // What holds the field while the page settles lets go as the page goes.
  useEffect(() => () => settle.current?.(), []);

  const refusedAt = refusedByPart(state.refused);
  // A change of the space requirements that Burro has not answered, once a search is open:
  // what says what failed stands in the box at the head of the page, which is out of sight
  // of whoever is among the space requirements, so each control whose change waits says so
  // where it stands. It is said from the failure until the next answer, and while the
  // change is tried again: the count of answers does not move while an edit waits.
  const cannotAnswer = state.failure !== null || !state.online;
  const [failedAt, setFailedAt] = useState<number | null>(null);
  const waits = !isEmpty(state.pending);
  if (waits && cannotAnswer && failedAt !== state.answers) setFailedAt(state.answers);
  if (!waits && failedAt !== null) setFailedAt(null);
  const unsent =
    open && waits && (cannotAnswer || failedAt === state.answers)
      ? { parts: partsOf(state.pending), says: state.online ? NOTICE.unsent : NOTICE.unsentOffline }
      : null;
  const repairs = repairsFor(state.failure, spec, state.pending);
  // What stands over the answer gives way further where the look has it do so, as it does
  // on a narrow screen whatever the search. Burro asks nothing, so nothing of his stands
  // over the answer to make it. Before a search there is no answer to give way to.
  const closer = open && gives === "always";
  // That areas can be compared is said beside what refines the search, on its line, once
  // there is a list to say it of. Where what stands over the answer gives way the list
  // says it, under its first result, as it does wherever a result is narrow.
  const listed = ranking !== null && ranking.ranked.length > 0;
  const besideWhatRefines = listed && !closer && over === "nothing" && invites("over");
  const unread = reading ? [] : (read?.unread ?? []);
  const isLatest = read !== null && read.at === state.answers;
  const unmet = (read?.unmet ?? []).filter((category) => category !== "other");
  // Nothing was applied, nothing was noticed that Burro took or left, and nothing was heard
  // that Burro has no data on: the words were read into nothing. What it has no data on was
  // heard, and a line under what it understood says so of each: seen in a browser, "Burro
  // could not read anything in what you typed" stood over "Burro has no data on broadband",
  // and both cannot be so.
  const readNothing =
    read !== null &&
    read.took === 0 &&
    read.left.length === 0 &&
    unmet.length === 0 &&
    (read.status === "off_topic" || nothingCameOf(read));
  // While a model reads what the rules left unread, it is not yet so that nothing could be
  // read: the page says that Burro is still reading, and says no more until it has.
  const nothingRead =
    !reading && isLatest && read !== null && !read.more && read.left.length === 0 && !changedTheSearch(read)
      ? readNothing
        ? NOTICE.nothingRead
        : read.rejected.length === 0 && read.edits > 0
          ? NOTICE.nothingChanged
          : null
      : null;
  // Nothing of what the box holds was read: what was sent is all that stands in it, and
  // nothing came of it. Words that were added after words the search had read are another
  // thing: some of what the box holds was then read, and some was not.
  const noneOfIt = readNothing && (state.box.shown === null || state.box.shown === 0);
  const noticed = read !== null && read.notice !== "none" && read.notice_text !== "";
  // Where the API has words of its own for it, they are in the notice, and are not said twice.
  const nothingSaid = noticed ? null : nothingRead;
  // Something was read, and a stretch of the text was not: the ranking leaves that stretch out.
  const partUnread = !reading && read !== null && read.partUnread && changedTheSearch(read);
  // Reasons are the ranking's only when they are for the same spec and the same release made both.
  const explained = reasonsAreIn(state);
  // The search came, and the reasons or a profile of one of its cards did not.
  const ofTheCards = failureOfTheCards(state);
  const served = servedTheRanking(state);
  const full =
    spec.commutes.length >= meta.limits.max_commutes ? PLACE.full(meta.limits.max_commutes) : null;
  // The map is coloured by a vibe only before a search. A ranking colours it by fit.
  const lens = useMemo((): Lens | null => {
    if (open || looksAt === null) return null;
    // The card of the word is in the first of the two ways in. While the second is chosen
    // it is not drawn, and the map says nothing of a word that is nowhere in sight.
    if (way !== "quick") return null;
    // A vibe that no area can be placed on colours nothing: the map was all dots, under a
    // legend that said it was coloured by the vibe.
    if (!isPlaced(meta, looksAt)) return null;
    const tag = meta.tags.find((one) => one.tag_id === looksAt && one.lens);
    const marks = bands.find((one) => one.tag_id === looksAt)?.marks;
    return tag === undefined || marks === undefined ? null : { tag, marks };
  }, [open, way, looksAt, meta, bands]);

  const nameOfPart = (key: string): string | null => {
    if (key === "tenure" || key === "budget" || key === "journeys") return REJECTED_PART[key];
    const [kind, id] = key.split(":", 2);
    if (kind === "feature") return meta.features.find((one) => one.feature_id === id)?.short_label ?? null;
    if (kind === "tag") return meta.tags.find((one) => one.tag_id === id)?.label ?? null;
    // A place the answers gave no name for is spoken of as "the place", and never by a stand-in.
    if (kind === "place" && id) return state.placeNames[id] ?? null;
    if (kind === "area") return areas.find((one) => one.area_id === id)?.name ?? null;
    return null;
  };
  // What was asked for that the data does not hold is said by name, directly under the
  // box. It is not said a second time among what was not applied.
  const missing = reading ? [] : missingFrom(read, state.refused, nameOfPart);
  // What a sentence asked for and was refused for its place or its number is named in the
  // line of what was left out, with why one press away. What a control asked for is said
  // beside the control, which shows what it was about, and in the list as it was.
  const ofTheWords = refusedOf(
    reading ? [] : refusals(read, null).filter((refusal) => !isSaidAsMissing(refusal, missing)),
    nameOfPart,
  );
  const notApplied = reading
    ? []
    : [...ofTheWords.rest, ...refusals(null, state.refused).filter((refusal) => !isSaidAsMissing(refusal, missing))];

  /**
   * Measures what stands in the place of the first result, as a sentence is sent and before
   * it gives way. A browser that lays nothing out, and a page with no result, measure nothing.
   */
  const hold = () => setRoom(first.current?.getBoundingClientRect().height || null);
  /** Sends what is in the box. From now until the box is changed, it holds what was sent. */
  /** A first search opens of what is sent, and the field is kept where it stands in the window. */
  const keepTheField = () => {
    stood.current = open ? null : fieldStands();
    sentFrom.current = stood.current;
  };
  const send = (text: string) => {
    keepTheField();
    hold();
    setShown(null);
    setLooksAt(null);
    void flow.submitText(text);
  };
  const retry = () => {
    keepTheField();
    hold();
    setShown(null);
    void flow.retry(prompt.current?.text() ?? "");
  };
  const sendAgain = () => send(prompt.current?.text() ?? "");
  // What rested on the text that was sent goes when the box changes: where the words of a
  // suggestion stand, and which stretch was not read.
  const typed = useCallback(() => {
    setShown(null);
    flow.boxChanged();
  }, [flow]);
  const startAgain = () => {
    sentFrom.current = null;
    setShown(null);
    setLooksAt(null);
    // The two ways in come back as they first stood: the first chosen, and every helper closed.
    setWay("quick");
    setDeep(false);
    setHelper(null);
    // Nothing of the search before is left: not the areas that were chosen from it to
    // compare, and not the area that was chosen on its map, which goes with the search.
    session?.compare.clear();
    flow.startAgain();
  };
  /** An area is chosen in the list or in the table, which say that it is shown in the list too. */
  const select = (areaId: string | null) => {
    setOnTheMap(null);
    flow.select(areaId);
  };
  /** An area is chosen on the map. Its card opens by the map, and the page stays where it is. */
  const choose = (areaId: string | null) => {
    setOnTheMap(areaId);
    flow.select(areaId);
  };
  const edit = (operations: Parameters<typeof flow.applyEdits>[0], made: How = "rank") => {
    setLooksAt(null);
    void flow.applyEdits(operations, made);
  };
  /**
   * A press is made, by pointer or by key. What stood under the one before is forgotten.
   * Where it is made in the second of the two ways in, and no search is open, what was
   * pressed is kept with where it stood: a search may open of it.
   */
  const pressed = (event: SyntheticEvent<HTMLElement>) => {
    forget();
    // A press made while a first search waits was aimed at the page as it then stood: as
    // Stop is, which stands beside the field.
    if (sentFrom.current !== null && open) sentFrom.current = fieldStands();
    const on = event.target;
    if (open || !(on instanceof HTMLElement) || refine.current?.contains(on) !== true) return;
    const parts = [on.closest<HTMLElement>(CONTROL) ?? on, document.activeElement];
    hand.current = parts.flatMap((part) =>
      part instanceof HTMLElement && refine.current?.contains(part) === true
        ? [{ part, top: part.getBoundingClientRect().top }]
        : [],
    );
  };
  /**
   * A setting is moved, or a place is added from the settings. Where no search is open,
   * and the look has a setting make the search, one opens of it, and the settings stay
   * open under it, as the part that refines the search: the person is in them. Where the
   * look has the answer brought into sight as a search opens of it, the press says so.
   * Where the second way in gathers, no search opens, and nothing is asked of the page.
   */
  const fromTheSettings = () => {
    if (open || how === "gather") return;
    flow.openSettings(true);
    if (opens === "answer") handsOver.current = "answer";
  };
  /**
   * The page was moved from under a press, and what stood there is another thing. A press
   * the browser counts as the second or a later one of a double press was aimed at what
   * was pressed: for as long as it may count one so, it lands on nothing.
   */
  const afterTheMove = (event: MouseEvent<HTMLElement>) => {
    if (event.detail < 2 || moved.current === null) return;
    if (performance.now() - moved.current > DOUBLE_PRESS_MS) return;
    event.preventDefault();
    event.stopPropagation();
  };
  /**
   * Selects, in the box, the next of these stretches of what was typed. The words stay in
   * the box: the page is given where they stand, and never what they are.
   */
  const show = (spans: readonly Span[]) => {
    const box = prompt.current;
    if (!box) return;
    const found = inTheBox(box.text(), spans);
    const next = shown === null || shown.among !== found.length ? 0 : shown.at % found.length;
    const stretch = found[next];
    if (stretch === undefined) {
      setShown({ at: 0, among: 0 });
      return;
    }
    box.select(stretch);
    setShown({ at: next + 1, among: found.length });
  };
  /** What was pressed goes with the press, so the focus is put on what the press changes. */
  const toUnderstood = () => document.getElementById(UNDERSTOOD)?.focus({ preventScroll: true });
  /**
   * A failure goes as it is tried again, and what was pressed goes with it. The focus is
   * put on Search, which stands over every failure of a search and is what is tried again.
   */
  const toSearch = () => {
    const search = () =>
      form.current?.querySelector<HTMLElement>('form button[type="submit"]')?.focus({ preventScroll: true });
    // Where the second way in is chosen Search is not drawn until a search opens of the press.
    search();
    then.current = search;
  };
  /** The search begins again with the box as it is: the focus is put in the box, where the words are. */
  const toTheBox = () => {
    const box = () => form.current?.querySelector("textarea")?.focus({ preventScroll: true });
    // Where the second way in is chosen the box is not drawn until the first is, as it begins again.
    box();
    then.current = box;
  };
  const tryAgain = () => {
    // What the second way in gathered is sent again, and no search opens of it: Search is
    // not drawn there, and the failure goes with what was pressed. The tab of the way has
    // the focus, under which what was said stood.
    if (!open && state.gathering) document.getElementById(tabIdOf(id, way))?.focus({ preventScroll: true });
    else toSearch();
    retry();
  };
  /**
   * Stop goes with the reading it ends. Over a search that is open Start again is drawn in
   * its place, and has the focus that Stop had. Where none is open, as while a first
   * sentence is read, nothing takes its place: the focus is put on Search, which stands
   * beside it and sends the words again, and is never left on nothing.
   */
  const stop = () => {
    if (read === null && ranking === null && state.untouched) toSearch();
    flow.stop();
  };
  const againFromAFailure = () => {
    toTheBox();
    startAgain();
  };
  /** Puts the focus on what opens the settings, once a search is open: the button of the part that refines it. */
  const toWhatRefines = () => refine.current?.querySelector<HTMLElement>(`:scope > * > ${OPENS_IT}`)?.focus();

  const openHelper = (next: HelperId | null) => {
    setHelper(next);
    // The map is coloured by the word whose card is open, and the card goes with the shelf.
    if (next !== "word") setLooksAt(null);
  };
  /** One of the two ways in is chosen. The second is drawn from the first time it is, and kept. */
  const chooseWay = (next: WayId) => {
    setWay(next);
    if (next === "deep") setDeep(true);
  };

  /**
   * Ranks the settings as they stand. The button goes as it is pressed, and the focus goes
   * to what opens the settings. Where a search opens of the press that is not drawn yet,
   * and the settings close over the answer as it opens.
   */
  const rank = () => {
    handsOver.current = "sight";
    if (open) toWhatRefines();
    else flow.openSettings(false);
    void flow.rankNow();
  };

  const table = (
    <AreaTable
      areas={areas}
      scores={ranking?.scores ?? []}
      filtered={ranking?.filtered ?? []}
      unranked={ranking?.unranked ?? []}
      emptySpec={ranking?.empty_spec ?? false}
      searched={ranking !== null}
      lens={lens}
      meta={meta}
      selectedId={state.selectedId}
      onSelect={select}
      onHover={flow.hover}
    />
  );

  // While the second way in gathers, what a search starts from is what was gathered: the
  // settings then draw themselves as they do before a search.
  const startsAs = useMemo(() => startsFrom(meta, spec, !open && state.gathering), [meta, spec, open, state.gathering]);

  const settings = (
    <SettingsPanel
      spec={spec}
      meta={startsAs}
      areas={areas}
      placeNames={state.placeNames}
      version={state.answers}
      refused={refusedAt}
      unsent={unsent}
      // They stand open wherever they are drawn: what opens and closes them is the page's.
      open
      busy={busy}
      full={full}
      onToggle={flow.openSettings}
      onEdit={(operations) => {
        fromTheSettings();
        edit(operations, how);
      }}
      onTenure={(tenure) => {
        // Before anything is asked for, a choice of renting or buying sends nothing, and opens no search.
        if (!state.untouched) fromTheSettings();
        void flow.setTenure(tenure, how);
      }}
      searchPlaces={flow.searchPlaces}
      onAddPlace={(place) => {
        fromTheSettings();
        void flow.addPlace(place, how);
      }}
      // Before a search the button that ranks by them is the page's own, and is cobalt:
      // it is the one that matters most in sight there. Once a search is open Search is in
      // sight over them, and theirs is plain.
      onRank={open && ranking === null && !busy ? rank : undefined}
      standing
    />
  );

  /** The button that ranks by the settings, in the second way in: the one that matters most in sight there. */
  const ranksBy = (
    <Press kind="go" className={styles.ranks} onPress={rank}>
      {SETTINGS.rank}
    </Press>
  );

  /**
   * What the second way opens with: a sentence that says what it is, and what makes the
   * search. It asks nothing of its own. Renting or buying and a place to reach stood here,
   * over the first two groups of the settings, which stand open and ask the same: seen in
   * a browser by three people, who could not tell which to answer. Where the look has the
   * button stand at the head of the way as well as at its foot, it stands here, under the
   * sentence that names it.
   */
  const opensWith = (
    <Frame kind="box" className={styles.asks}>
      <p className={styles.deep}>{DEEP.lead}</p>
      {button === "both" ? ranksBy : null}
    </Frame>
  );

  /**
   * The field that finds an area by its name, at the foot of the second way. An area is a
   * link to its page, and no part of a search: so it stands after the button that makes
   * the search, and finds no place to reach, which the settings find.
   */
  const findsAnArea =
    finds === "foot" ? (
      <Frame kind="box" className={styles.finds}>
        <PlaceCombobox
          search={flow.searchPlaces}
          onPick={() => undefined}
          label={FIND_AREA.labelAlone}
          // Where the data names no place the settings have no field for one, and a place
          // would be typed here: so the field says why it finds none.
          hint={meta.holds.journeys ? DEEP.finds : FIND_AREA.hintAlone}
          noPlaces
          areas
        />
      </Frame>
    ) : null;

  /**
   * The helpers, in the order they stand in. Each opens what stood open on the first
   * screen, and one that the data gives nothing to offer is not drawn.
   */
  const helpers: Helper<HelperId>[] = [];
  const examples = examplesFor(meta);
  if (examples.length > 0) {
    helpers.push({
      id: "example",
      label: HELPERS.example,
      children: <Examples examples={examples} onUse={(example) => prompt.current?.fill(example)} />,
    });
  }
  // A word that no area can be placed on cannot be added, so a shelf of such words alone
  // is nothing to start from.
  if (placedOf(meta, meta.tags).length > 0) {
    helpers.push({
      id: "word",
      label: HELPERS.word,
      children: (
        <Shelf
          tags={meta.tags}
          features={meta.features}
          recipes={meta.recipes}
          geometry={state.geometry}
          bands={bands}
          open={looksAt}
          onOpen={setLooksAt}
          onAdd={(operations) => {
            handsOver.current = "understood";
            edit(operations);
          }}
        />
      ),
    });
  }
  // While the first sentence of a search is read nothing is understood yet, and nothing
  // holds the place of it: Burro hops where the answer will stand, and the line says so.
  // Nor is it while what Burro took of the sentence waits to be ranked: the search the
  // service last returned holds none of it yet, and what was understood comes with the answer.
  const understood = open && !(reading && ranking === null && (read === null || !isEmpty(state.pending)));
  // What Burro noticed and left out of the search, which one line under what it understood
  // names, with the words that were not read where something of the sentence was.
  const leftOut = reading ? [] : [...leftOutOf(read), ...ofTheWords.named];
  // The way to see, in the box, the words that were not read. Where nothing at all was read
  // the page says so, by the box, and says nothing of some of the words: seen in a browser,
  // "Nothing in that could be read" stood over "Some of your words were not read", and both
  // cannot be so. What would be shown in the box is then all that it holds.
  const showsWords = unread.length > 0 && !noneOfIt;
  const theWayToTheWords = showsWords ? (
    <Small onPress={() => show(unread)}>
      {shown !== null && shown.among > 1 ? SUGGEST.showNextUnread : SUGGEST.showUnread}
    </Small>
  ) : null;
  /** What the way to the words did, once it was pressed: which words are selected in the box. */
  const wordsShown =
    shown === null ? "" : shown.among === 0 ? NOTICE.partNotFound : NOTICE.partShown(shown.at, shown.among);
  // What Burro says of the search stands in the box. Before a search the box is in the
  // first way in: while the second is chosen, what he says stands at the head of that,
  // so that a failure, or that the person is offline, is said where they are.
  const saidIn: "box" | "deep" = open || way === "quick" ? "box" : "deep";

  const says = (
    <div className={styles.says} data-open={open}>
      <StatusLine
        phase={phase}
        ranking={ranking}
        areas={areas}
        moved={state.moved}
        was={state.rankedBefore}
        gaveWay={state.gaveWay}
        budgetWent={state.budgetWent}
        visiting={spec.tenure === "visit"}
        // Where what stands over the answer gives way, the line stands in no frame of its own.
        frame={closer ? "none" : undefined}
        // The line speaks of the ranking on screen, so it is given the spec that was ranked.
        spec={ranking !== null && state.rankedHash === state.specHash ? spec : undefined}
        // Once a search is open the line keeps its room, and says so where nothing is ranked.
        open={open}
        // An answer that is said in the words of the last is said again.
        answers={state.answers}
      />

      {shows === "offline" ? (
        <div data-failure="">
          <OfflineLine waiting={!isEmpty(state.pending)} />
        </div>
      ) : null}
      <NotInData missing={missing} meta={meta} />
      {/* What Burro left out, and that words were not read, in one line that asks nothing.
          It changes what the ranking means, so it stands beside the box and over what was
          understood, where that a part was not read has stood since it was missed under the
          chips. Where nothing is ranked it stands open: no answer waits under it. */}
      <LeftOut
        // It is of one reading, and is closed as the next begins: what a person opened
        // stood open in every search after it, and over the answer of each.
        key={read === null ? "none" : `of ${read.of}`}
        things={leftOut}
        words={partUnread}
        meta={meta}
        startsOpen={ranking === null && !asked}
        did={partUnread ? wordsShown : ""}
      >
        {partUnread ? theWayToTheWords : null}
      </LeftOut>
      {state.degraded && !reading ? (
        <div className={styles.degraded} data-failure="">
          {/* A reading is held while the next is asked for. Where the page is a form, nothing
              read the words in the box, so nothing is said to have refused them. */}
          {/* Before a search the settings stand in the second way in, which the line names. */}
          <StateLine>
            {read?.model_refused === true && shows !== "form"
              ? NOTICE.refused
              : open
                ? NOTICE.degraded
                : UNREAD.before}
          </StateLine>
          {/* Words that were not read can always be tried again, from the box. Words the
              rules read in place of a model were read, and there is nothing to try again. */}
          {read?.degraded !== true || shows === "form" ? (
            <Press
              onPress={() => {
                toSearch();
                (shows === "form" ? retry : sendAgain)();
              }}
            >
              {PROMPT.tryAgain}
            </Press>
          ) : null}
        </div>
      ) : null}
      {shows === "block" && state.failure !== null ? (
        <div data-failure="">
          <ErrorBlock
            failure={state.failure}
            notUpdated={ranking !== null}
            repairs={repairs}
            nameOf={nameOfPart}
            onRetry={tryAgain}
            onStartAgain={againFromAFailure}
            onEdit={edit}
          />
        </div>
      ) : null}
      {/* The card says what it lacks. Here is why, in the API's words with the id to
          quote, and "Try again", which ranks again and asks for what is missing. */}
      {shows === "none" && ofTheCards !== null ? (
        <ErrorBlock
          failure={ofTheCards}
          notUpdated={false}
          onRetry={tryAgain}
          onStartAgain={againFromAFailure}
          onEdit={edit}
        />
      ) : null}

      {read !== null && !reading ? <NoticeBlock notice={read.notice} text={noticeOf(read)} /> : null}
      {nothingSaid !== null ? <StateLine>{nothingSaid}</StateLine> : null}

      {understood ? (
        <>
          <ChipRow
            id={UNDERSTOOD}
            spec={spec}
            assumed={state.assumed}
            quoted={state.quoted}
            tenurePicked={state.tenurePicked}
            placeNames={state.placeNames}
            meta={meta}
            areas={areas}
            version={state.answers}
            refused={refusedAt}
            readBy={read?.interpreter ?? null}
            onEdit={edit}
            onTenure={(tenure) => void flow.setTenure(tenure)}
          />
          {read !== null && !reading ? <UnmetList unmet={unmet} /> : null}
          <RejectedList refusals={notApplied} nameOf={nameOfPart} meta={meta} />
        </>
      ) : null}
    </div>
  );

  /**
   * That Burro reads still, and the way to see the words that nothing came of. It stands
   * directly under the box and what Burro says, in a part of its own, and asks nothing.
   * Where something was read and a stretch was not, the line of what was left out says so.
   */
  const offered = (
    <div className={styles.noticed}>
      {/* While a model reads what the rules left unread, the page says so: what it reads
          is taken as what the rules read was, and the ranking is worked out again. */}
      {!reading && read !== null && read.more ? (
        <p className={styles.still} role="status">
          {SUGGEST.reading}
        </p>
      ) : null}
      {showsWords && !partUnread ? (
        <>
          <div className={styles.unread}>
            <p>{SUGGEST.unread}</p>
            {theWayToTheWords}
          </div>
          {/* It is on the page before it says anything, so that a screen reader is told when it does. */}
          <p className={styles.shown} role="status">
            {wordsShown}
          </p>
        </>
      ) : null}
    </div>
  );

  /**
   * The button, held at the foot of the window while its own place is under it, with what
   * Burro says of what could not be sent over it: a failure, or that the person is
   * offline. Both are in sight wherever a person is among the groups. What Burro says
   * stood at the head of the way, as far over a person who had chosen as the button
   * stood under them.
   */
  const heldInSight = (
    <div className={styles.held}>
      {saidIn === "deep" ? says : null}
      <Press ref={held} kind="go" className={styles.ranks} onPress={rank}>
        {SETTINGS.rank}
      </Press>
    </div>
  );

  const nothingMatches = ranking !== null && ranking.ranked.length === 0;
  // The order of the page is the order it is drawn in, for the screen there is.
  const order = orderOf(screen, open, refines);
  useFocusKept(page, order.join(" "));
  /** One list of results, drawn in two parts: the first result before the map, and the rest after it. */
  const list = (part: Part) => (
    <ResultList
      part={part}
      ranked={ranking?.ranked ?? null}
      areas={areas}
      // Where every area sits, which came with the page. The town of a result is drawn from
      // it, so that a part of one is blank for what is not known of its area, and never
      // for what was not asked for: a strip holds what was asked for, and two more.
      bands={bands}
      explanations={explained ? state.explanations : []}
      explained={explained}
      explainFailed={reasonsFailure(state) !== null}
      facts={state.facts}
      details={state.details}
      detailsFailed={profilesFailed(state)}
      geometry={state.geometry}
      spec={spec}
      meta={meta}
      served={served}
      placeNames={state.placeNames}
      noFit={ranking?.empty_spec ?? false}
      unranked={ranking?.unranked ?? []}
      areasRanked={ranking?.areas_ranked ?? 0}
      areasListed={ranking?.areas_listed ?? 0}
      busy={busy}
      over={over}
      // Where the page does not say beside what refines the search that areas can be
      // compared, and the look has it said, the list says it under its first result.
      inviteStands={closer && invites("under") ? "under" : undefined}
      // What was chosen on the map is shown in the list when the card of the map is asked to.
      selectedId={state.selectedId !== null && state.selectedId === onTheMap ? null : state.selectedId}
      onSelect={(areaId) => {
        select(areaId);
        // On a narrow screen the map may be some way from a result. It is brought into
        // view. The focus is the result's to give: to the box the map opens for the area,
        // and it stays on the button that was pressed where no map is drawn.
        if (typeof map.current?.scrollIntoView === "function") {
          map.current.scrollIntoView({ block: "nearest" });
        }
      }}
      onHover={flow.hover}
      // What a result sends is that its area is hidden, and the result goes with the press.
      // The focus goes to what Burro understood, where the area then stands to be shown again.
      onEdit={(operations) => {
        toUnderstood();
        edit(operations);
      }}
    />
  );

  /**
   * The parts of the page, each by its name. They are put in the order the screen draws
   * them in, which `order.ts` says: so the order of the page is the order it is drawn in,
   * for a keyboard and for whoever hears the page as for the eye.
   */
  const parts: Readonly<Record<PartOfThePage, ReactNode>> = {
    form: (
      <section key="form" ref={form} className={styles.form} aria-label={SEARCH.formLabel}>
        {/* Two ways in, for beginning. Once a search is open they have become one search. */}
        {open ? null : (
          <Ways
            label={WAYS.label}
            name={id}
            ways={WAY_IDS.map((one) => ({ id: one, label: WAYS[one] }))}
            chosen={way}
            onChoose={chooseWay}
          />
        )}
        {/* The first way in. It holds the box, which stays where it is as a search opens
            and as one begins again: so what is typed is never drawn anew. */}
        <div className={styles.panel} {...(open ? {} : panelOf(id, "quick", way))}>
          {/* With scripts off no tab is drawn, and each way stands under its name. */}
          {open ? null : (
            <noscript>
              <h2 className={styles.named}>{WAYS.quick}</h2>
            </noscript>
          )}
          <PromptBox
            ref={prompt}
            maxText={meta.limits.max_text}
            busy={reading}
            open={open}
            onSubmit={send}
            onStop={stop}
            onStartAgain={startAgain}
            onTyped={typed}
            refusal={shows === "box" && state.failure?.kind === "api" ? state.failure.message : null}
            hint={PROMPT.hintFor(meta.holds)}
            // The first sentence the data can answer the whole of, as an example of one.
            example={examples[0] ?? null}
            narrow={screen === "narrow"}
          >
            {saidIn === "box" ? says : null}
          </PromptBox>
          {offered}
          {/* What else a quick search can begin from is one press away, in one line
              under the box, and goes when a search opens. */}
          {open ? null : <Helpers label={HELPERS.label} helpers={helpers} open={helper} onOpen={openHelper} />}
        </div>
      </section>
    ),

    // The settings. Before a search they stand open in the second way in, under what it
    // says of itself. Once a search is open they are the part that refines it, closed
    // until it is pressed. They are one part of the page: so where the look has a search
    // open of a setting that was moved, they are as they were.
    refine: (
      <div
        key="refine"
        ref={refine}
        className={styles.refine}
        data-standing={!open}
        {...(open ? {} : panelOf(id, "deep", way))}
      >
        {saidIn === "deep" && button !== "held" ? <div className={styles.told}>{says}</div> : null}
        {!open && deep ? opensWith : null}
        {/* Once a search is open the fold is drawn when there is something to refine: while
            a first sentence is read nothing is understood yet, and what opens the
            settings stood between the box and Burro, and went down the page as the chips
            came in over it. */}
        {(open ? understood : deep) ? (
          <Disclosure
            label={REFINE.label}
            // Before a search they stand open, and nothing closes them: the style sheet draws no button.
            open={!open || state.settingsOpen}
            onToggle={(next) => {
              if (open) flow.openSettings(next);
            }}
            className={styles.fold}
            bring
          >
            {settings}
          </Disclosure>
        ) : null}
        {/* That areas can be compared, before anybody has chosen one: beside what refines
            the search, on its line, so that nothing stands between that line and the
            first result. It holds nothing that can be pressed. */}
        {besideWhatRefines ? (
          <p className={styles.compares}>
            <Invite stands="over" />
          </p>
        ) : null}
        {!open && deep ? (button === "held" ? heldInSight : ranksBy) : null}
        {!open && deep ? findsAnArea : null}
      </div>
    ),

    // With scripts off no tab can be pressed, so the second way stands under the first, under its name.
    unscripted: open ? null : (
      <noscript key="unscripted">
        <div className={styles.unscripted}>
          <h2 className={styles.named}>{WAYS.deep}</h2>
          {opensWith}
          {settings}
          {ranksBy}
          {findsAnArea}
        </div>
      </noscript>
    ),

    // The answer comes first: the first result stands directly after what Burro says of
    // the search, and before the map.
    results: open ? (
      <section
        key="results"
        ref={results}
        id={PANEL.list}
        className={styles.results}
        tabIndex={-1}
        aria-labelledby="results-title"
      >
        {/* A numbered list of areas under the line that says how many were ranked says
            what it is. The heading is kept for whoever hears the page. */}
        <h2 id="results-title" className="visually-hidden">
          {RESULTS.title}
        </h2>
        {/* While a sentence is read Burro hops where the results will stand, and while a
            first ranking that a control asked for is worked out. What the search holds
            is drawn over him then, so his box holds the room of a first result alone. */}
        {reading ? <Wait held={room} room={ROOM} /> : asked ? <Wait held={null} of="ranking" /> : null}
        {/* What stood there gives way to him and is kept, with whatever of it was
            opened, to stand there again if the sentence changes nothing of it. On a
            first search nothing stood there, and nothing holds the place of it. */}
        {(reading || asked) && ranking === null ? null : (
          <div ref={first} className={styles.first} hidden={reading}>
            {ranking !== null && nothingMatches ? (
              <NothingMatches
                filtered={ranking.filtered}
                unranked={ranking.unranked}
                spec={spec}
                areas={areas}
                placeNames={state.placeNames}
                meta={meta}
                // The block goes once areas pass, and the way out with it. The focus
                // goes to what Burro understood, which is what the press changes.
                onEdit={(operations) => {
                  toUnderstood();
                  edit(operations);
                }}
              />
            ) : (
              list("first")
            )}
          </div>
        )}
      </section>
    ) : null,

    // One press away, after the first result: sharing, once there is a ranking.
    tools:
      ranking !== null ? (
        <div key="tools" className={styles.tools}>
          <SharePanel
            spec={spec}
            specHash={state.specHash}
            meta={meta}
            areas={areas}
            create={flow.createShare}
            held={madeLink}
            onMade={keepLink}
          />
          {/* The button that keeps a search, which draws nothing where accounts are off. */}
          <KeepSearch />
        </div>
      ) : null,

    map: (
      <div
        key="map"
        ref={map}
        id={PANEL.map}
        className={styles.map}
        role="region"
        aria-label={MAP.label}
        // The link that skips to the map puts the focus here. It is no stop of its own.
        tabIndex={-1}
      >
        <a className={`${styles.skip} target`} href="#after-map">
          {SEARCH.skipMap}
        </a>
        {/* What the map says in words beside it is read on cream, as all else is. */}
        <div className={styles.slip}>
          <MapView
            geometry={state.geometry}
            geometryFailed={state.geometryFailed}
            areas={areas}
            scores={ranking?.scores ?? []}
            ranked={ranking?.ranked ?? []}
            filtered={ranking?.filtered ?? []}
            unranked={ranking?.unranked ?? []}
            emptySpec={ranking?.empty_spec ?? false}
            selectedId={state.selectedId}
            hoveredId={state.hoveredId}
            onSelect={choose}
            onHover={flow.hover}
            onShowInList={(areaId) => {
              // The list is told which area was chosen on the map, and brings it into sight.
              setOnTheMap(null);
              setReveal((last) => ({ areaId, at: (last?.at ?? 0) + 1 }));
            }}
            lens={lens}
            table={table}
            // Before a search, where the page is one column, it stands over the two ways in, low.
            low={!open}
          />
        </div>
        {/* Where the link that skips the map leads. It says what it is, to whoever hears the
            page: the focus landed on a thing with no name and no words. */}
        <span id="after-map" tabIndex={-1}>
          <span className="visually-hidden">{SEARCH.pastMap}</span>
        </span>
      </div>
    ),

    // The rest of the results, from the second. They come after the map, and on a wide
    // screen stand under the first result, beside it. While a sentence is read they stay
    // where they are. On a first search there are none, and nothing holds their place.
    rest:
      open && !nothingMatches && !((reading || asked) && ranking === null) ? (
        <div key="rest" className={styles.rest}>
          {list("rest")}
        </div>
      ) : null,
  };

  return (
    // It says whether a search is open, so that the banner over the page can give way to the answer.
    // It hears that a press or a key has begun, before what is pressed hears it, and does nothing to either.
    <div
      ref={page}
      className={styles.search}
      // It stands boxes of its own on the grass, so the shell draws none round it.
      data-dressed=""
      data-open={open}
      data-search={open ? "open" : "closed"}
      // Where the part that refines a search stands on a narrow screen, for the style sheet.
      data-refine={refines}
      // Whether what stands over the answer gives way further, for the style sheet.
      data-closer={closer}
      onPointerDownCapture={pressed}
      onKeyDownCapture={pressed}
      onClickCapture={afterTheMove}
    >
      {/* Before a search there are no results to skip to, and no link that leads nowhere. */}
      {open || busy ? (
        <a className={`${styles.skip} target`} href={`#${PANEL.list}`}>
          {SEARCH.skipToResults}
        </a>
      ) : null}
      <a className={`${styles.skip} target`} href={`#${PANEL.map}`}>
        {SEARCH.skipToMap}
      </a>
      {/* Once a search is open the title gives way to the answer. It is still the heading of
          the page to whoever hears it, and says what the page is: the search page, or a
          search that came from a link, whose first result stood out of sight under its title. */}
      {open ? (
        <h1 className="visually-hidden">{shared ? SHARED.title : SEARCH.title}</h1>
      ) : (
        <Frame kind="box" className={styles.head}>
          {/* Before a search Burro sits beside the heading, still. He is drawn beside no other. */}
          <Burro pose="sits" />
          <h1 className={styles.title}>{shared ? SHARED.title : SEARCH.title}</h1>
          {/* What the page is for is said to whoever has not searched yet. After that the answer
              comes first. Who it is for is said on every screen, and how it is done on all
              but a narrow one, where the map and the two ways in are what follows. */}
          <p className={styles.lead}>
            {SEARCH.forWhom}{" "}
            <span className={styles.how}>{leadFor(meta.holds).slice(SEARCH.forWhom.length).trim()}</span>
          </p>
        </Frame>
      )}
      {state.shared !== null ? (
        <div className={styles.shared}>
          <SharedHeader
            shared={state.shared}
            release={served.release_id}
            hasPlaces={spec.commutes.length > 0}
            titled={!shared}
          />
        </div>
      ) : null}

      <div ref={columns} className={styles.columns}>
        {/* Each part is named, and they come in the order the screen draws them in: a part
            that changes its place in the page is the part it was, with all that it holds. */}
        {order.map((part) => parts[part])}
      </div>
      {/* It holds the tray and is no box of its own, so that the tray is laid out as the page's. */}
      <div className={styles.tray}>
        <CompareTray />
      </div>
    </div>
  );
}
