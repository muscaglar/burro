"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState, type RefObject } from "react";

import { ACCOUNT } from "@/content/account";
import type { Failure } from "@/lib/api/failure";
import type { KeptSearch, PreferenceSpec, Switch } from "@/lib/api/schema";
import type { AccountClient } from "@/lib/account/client";
import { noteKeeps } from "@/lib/account/recent";
import { readableDate } from "@/lib/format";

import { Box, Failed, Tick } from "../AccountParts/parts";
import parts from "../AccountParts/parts.module.css";
import { Press } from "../kit/Press/Press";
import { Skeleton } from "../Skeleton/Skeleton";
import styles from "./Account.module.css";
import { useListed } from "./listed";

type Client = Pick<
  AccountClient,
  "listSearches" | "forgetSearch" | "keepSearch" | "listRecent" | "forgetRecent" | "setPreferences"
>;

interface Props {
  readonly client: Client;
  /** Opens a search that was kept, and leads to the search page. It answers with why it could not, or with `null`. */
  readonly open: (spec: PreferenceSpec) => Promise<Failure | null>;
}

/** What is being done to a row, and to which: one thing at a time. */
interface Doing {
  readonly what: "open" | "remove" | "save";
  readonly id: string;
}

/** What became of the last thing that was done to a row. */
interface Became {
  readonly id: string;
  readonly title: string;
  readonly failure: Failure;
}

/** True of a search that can be searched again as it is: the service says so, and gives its spec. */
const opens = (search: KeptSearch): search is KeptSearch & { readonly spec: PreferenceSpec } =>
  search.state === "ok" && search.spec !== null;

/** What can be pressed in a list, in the order a keyboard comes to it. */
const PRESSED = "button, a[href]";

/**
 * Hands the focus on when a row goes with the press that was made in it: to the row that
 * now stands where it stood, or the one before it, or where there is none to the heading
 * of the box. So it is never left on nothing. It answers with what a press tells it: the
 * place of the row that goes.
 */
function useFocusHandedOn(
  list: RefObject<HTMLDivElement | null>,
  heading: RefObject<HTMLHeadingElement | null>,
  listed: unknown,
): (at: number) => void {
  const went = useRef<number | null>(null);

  // Before the page is drawn, so that the focus is never seen to be on nothing.
  useLayoutEffect(() => {
    const at = went.current;
    if (at === null) return;
    went.current = null;
    const rows = [...(list.current?.querySelectorAll<HTMLElement>(":scope > ul > li") ?? [])];
    const next = rows[Math.min(at, rows.length - 1)]?.querySelector<HTMLElement>(PRESSED);
    (next ?? heading.current)?.focus();
  }, [list, heading, listed]);

  return useCallback((at: number) => {
    went.current = at;
  }, []);
}

/**
 * The searches a person has kept, and the last ones they made.
 *
 * A search is what Burro understood, and its name is the service's, worked out from that:
 * neither holds a word the person typed. A search is opened by loading it into the search
 * of the tab and ranking it now, as the search of a shared link is. One that the service
 * says can no longer be searched as it is says why, and cannot be opened.
 *
 * Whether the last searches are kept is the person's to choose, by a tick. What the tick
 * says is what the service last said, and never what was pressed: a change that the
 * service did not take is not shown as taken.
 *
 * One thing is done at a time. What is pressed says that it is off while it waits, and
 * keeps the focus. A row that goes with the press hands the focus on.
 */
export function Searches({ client, open }: Props) {
  const saved = useListed(client.listSearches);
  const recent = useListed(client.listRecent);
  const [doing, setDoing] = useState<Doing | null>(null);
  const [became, setBecame] = useState<Became | null>(null);
  const [said, setSaid] = useState({ saved: "", recent: "" });
  // What the box was last pressed to, until the service has answered. `null` once it has.
  const [wished, setWished] = useState<boolean | null>(null);
  const [unset, setUnset] = useState<Failure | null>(null);
  const savedList = useRef<HTMLDivElement>(null);
  const savedHeading = useRef<HTMLHeadingElement>(null);
  const recentList = useRef<HTMLDivElement>(null);
  const recentHeading = useRef<HTMLHeadingElement>(null);
  const savedGoes = useFocusHandedOn(savedList, savedHeading, saved.listed);
  const recentGoes = useFocusHandedOn(recentList, recentHeading, recent.listed);

  // Whether the last searches are kept is what the search page asks before it sends one to be kept.
  useEffect(() => {
    if (recent.listed.kind === "listed") noteKeeps(recent.listed.data.kept);
  }, [recent.listed]);

  const begin = (what: Doing["what"], id: string) => {
    setDoing({ what, id });
    setBecame(null);
    setSaid({ saved: "", recent: "" });
  };

  const openOne = async (search: KeptSearch & { readonly spec: PreferenceSpec }) => {
    if (doing !== null) return;
    begin("open", search.search_id);
    const failure = await open(search.spec);
    setDoing(null);
    if (failure !== null && failure.kind !== "aborted") {
      setBecame({ id: search.search_id, title: ACCOUNT.searches.couldNotOpen, failure });
    }
  };

  const remove = async (search: KeptSearch, at: number) => {
    if (doing !== null) return;
    begin("remove", search.search_id);
    const answer = await client.forgetSearch({ search_id: search.search_id });
    setDoing(null);
    if (!answer.ok) {
      if (answer.failure.kind !== "aborted") {
        setBecame({ id: search.search_id, title: ACCOUNT.searches.couldNotRemove, failure: answer.failure });
      }
      return;
    }
    // The row goes, and what was pressed with it.
    savedGoes(at);
    saved.set(answer.data);
    setSaid({ saved: ACCOUNT.searches.removed, recent: "" });
  };

  const save = async (search: KeptSearch & { readonly spec: PreferenceSpec }) => {
    if (doing !== null) return;
    begin("save", search.search_id);
    const answer = await client.keepSearch({ spec: search.spec });
    setDoing(null);
    if (!answer.ok) {
      if (answer.failure.kind !== "aborted") {
        setBecame({ id: search.search_id, title: ACCOUNT.recent.couldNotSave, failure: answer.failure });
      }
      return;
    }
    setSaid({ saved: "", recent: ACCOUNT.recent.saved });
    // What is saved is listed again, under what is there until it has come.
    await saved.ask(true);
  };

  const keep = async (on: boolean) => {
    if (wished !== null) return;
    // The box says what was pressed at once, as a box does, and keeps the focus. What is
    // listed under it is what the service holds, and changes when the service has answered.
    setWished(on);
    setUnset(null);
    const wanted: Switch = on ? "on" : "off";
    const answer = await client.setPreferences({ keep_recent: wanted });
    if (!answer.ok) {
      // It was not taken: the box goes back to what the service holds, and the page says why.
      setWished(null);
      if (answer.failure.kind !== "aborted") setUnset(answer.failure);
      return;
    }
    // What is listed is what is kept now: with the tick taken off, nothing is.
    await recent.ask(true);
    setWished(null);
  };

  const forget = async () => {
    if (doing !== null) return;
    begin("remove", "");
    const answer = await client.forgetRecent();
    setDoing(null);
    if (!answer.ok) {
      if (answer.failure.kind !== "aborted") {
        setBecame({ id: "", title: ACCOUNT.recent.couldNotForget, failure: answer.failure });
      }
      return;
    }
    // Every row goes, and the button that was pressed with them.
    recentGoes(0);
    recent.set(answer.data);
    setSaid({ saved: "", recent: ACCOUNT.recent.forgotten });
  };

  const waits = doing !== null;
  /** What is said of what is being done, to whoever hears the page. */
  const doingSaid = (ids: readonly string[]) =>
    doing === null || !ids.includes(doing.id)
      ? ""
      : doing.what === "open"
        ? ACCOUNT.searches.opening
        : doing.what === "save"
          ? ACCOUNT.recent.saving
          : doing.id === ""
            ? ACCOUNT.recent.forgetting
            : ACCOUNT.searches.removing;

  const row = (search: KeptSearch, at: number, among: "saved" | "recent") => {
    const { name } = search;
    return (
      <li key={search.search_id}>
        <div className={styles.row}>
          <div className={styles.of}>
            {/* The name is the service's: what was understood, said in a line. */}
            <p className={styles.name}>{name}</p>
            <p className={parts.quiet}>
              {(among === "saved" ? ACCOUNT.searches.kept : ACCOUNT.recent.made)(readableDate(search.kept_at))}
            </p>
            {opens(search) ? null : <p>{ACCOUNT.searches.state[search.state === "ok" ? "unreadable" : search.state]}</p>}
          </div>
          <div className={styles.does}>
            {opens(search) ? (
              <Press
                name={ACCOUNT.searches.of(ACCOUNT.searches.open, name)}
                off={waits}
                onPress={() => void openOne(search)}
              >
                {ACCOUNT.searches.open}
              </Press>
            ) : null}
            {among === "recent" && opens(search) ? (
              <Press name={ACCOUNT.searches.of(ACCOUNT.recent.save, name)} off={waits} onPress={() => void save(search)}>
                {ACCOUNT.recent.save}
              </Press>
            ) : null}
            {among === "saved" ? (
              <Press
                kind="stop"
                name={ACCOUNT.searches.of(ACCOUNT.searches.remove, name)}
                off={waits}
                onPress={() => void remove(search, at)}
              >
                {ACCOUNT.searches.remove}
              </Press>
            ) : null}
          </div>
          {became !== null && became.id === search.search_id ? (
            <div className={styles.under}>
              <Failed title={became.title} failure={became.failure} />
            </div>
          ) : null}
        </div>
      </li>
    );
  };

  const savedIds = saved.listed.kind === "listed" ? saved.listed.data.searches.map((search) => search.search_id) : [];
  const recentIds = recent.listed.kind === "listed" ? recent.listed.data.searches.map((search) => search.search_id) : [];

  return (
    <>
      <Box title={ACCOUNT.searches.title} heading={savedHeading}>
        <p>{ACCOUNT.searches.named}</p>
        {saved.listed.kind === "opening" ? (
          <div aria-busy="true">
            <Skeleton lines={3} />
          </div>
        ) : saved.listed.kind === "failed" ? (
          <Failed title={ACCOUNT.searches.couldNotList} failure={saved.listed.failure}>
            <Press onPress={() => void saved.ask()}>{ACCOUNT.tryAgain}</Press>
          </Failed>
        ) : saved.listed.data.searches.length === 0 ? (
          <p>{ACCOUNT.searches.none}</p>
        ) : (
          <>
            <p className={parts.quiet}>
              {ACCOUNT.searches.count(saved.listed.data.searches.length, saved.listed.data.most)}
            </p>
            <div ref={savedList} className={styles.list}>
              <ul className={styles.rows} aria-label={ACCOUNT.searches.list}>
                {saved.listed.data.searches.map((search, at) => row(search, at, "saved"))}
              </ul>
            </div>
          </>
        )}
        <p className={parts.said} role="status">
          {doingSaid(savedIds) || said.saved}
        </p>
      </Box>

      <Box title={ACCOUNT.recent.title} heading={recentHeading}>
        {recent.listed.kind === "opening" ? (
          <div aria-busy="true">
            <Skeleton lines={3} />
          </div>
        ) : recent.listed.kind === "failed" ? (
          <Failed title={ACCOUNT.recent.couldNotList} failure={recent.listed.failure}>
            <Press onPress={() => void recent.ask()}>{ACCOUNT.tryAgain}</Press>
          </Failed>
        ) : (
          <>
            <Tick
              says={ACCOUNT.recent.keep(recent.listed.data.most)}
              hint={ACCOUNT.recent.hint}
              ticked={wished ?? recent.listed.data.kept}
              off={wished !== null}
              onTick={(ticked) => void keep(ticked)}
            />
            {unset === null ? null : <Failed title={ACCOUNT.recent.couldNotSet} failure={unset} />}
            {!recent.listed.data.kept ? (
              <p>{ACCOUNT.recent.off}</p>
            ) : recent.listed.data.searches.length === 0 ? (
              <p>{ACCOUNT.recent.none}</p>
            ) : (
              <>
                <div ref={recentList} className={styles.list}>
                  <ul className={styles.rows} aria-label={ACCOUNT.recent.list}>
                    {recent.listed.data.searches.map((search, at) => row(search, at, "recent"))}
                  </ul>
                </div>
                <div className={parts.ways}>
                  <Press kind="stop" off={waits} onPress={() => void forget()}>
                    {ACCOUNT.recent.forget}
                  </Press>
                </div>
              </>
            )}
            {became !== null && became.id === "" ? <Failed title={became.title} failure={became.failure} /> : null}
          </>
        )}
        <p className={parts.said} role="status">
          {doingSaid(["", ...recentIds]) || said.recent}
        </p>
      </Box>
    </>
  );
}
