"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore } from "react";

import { ACCOUNT } from "@/content/account";
import { api, type Client } from "@/lib/api/client";
import { failed, type Failure } from "@/lib/api/failure";
import type { Handed } from "@/lib/api/handed";
import type { AreaSummary, Me, PreferenceSpec } from "@/lib/api/schema";
import { account } from "@/lib/account/account";
import type { AccountClient } from "@/lib/account/client";
import { NOT_SIGNED_IN } from "@/lib/account/client";
import { useGo } from "@/lib/account/go";
import { openKept } from "@/lib/account/open";
import { noteOpened } from "@/lib/account/opened";
import { accountPaths } from "@/lib/account/paths";
import { noteSignedIn, noteSignedOut, subscribeToWho, UNKNOWN, whoIs } from "@/lib/account/who";
import { paths } from "@/lib/paths";
import { SearchProvider } from "@/lib/search/store";
import { SessionBoundary, useSessionIfAny } from "@/lib/session/session";

import { Box, Failed, Page } from "../AccountParts/parts";
import parts from "../AccountParts/parts.module.css";
import { Press } from "../kit/Press/Press";
import { Skeleton } from "../Skeleton/Skeleton";
import { Copy } from "./Copy";
import { Remove } from "./Remove";
import { Searches } from "./Searches";
import { Sessions } from "./Sessions";

interface Props {
  /** What a search needs to be opened: the vocabulary, the defaults and the limits. From route 11, at build. */
  readonly meta: Handed;
  /** Every area of the release, from route 4, at build. */
  readonly areas: readonly AreaSummary[];
  /** The routes of accounts to call. A test passes its own. */
  readonly client?: AccountClient;
  /** The API to rank a search with. A test passes its own. */
  readonly ranks?: Client;
}

type Stage =
  | { readonly kind: "opening" }
  | { readonly kind: "out" }
  | { readonly kind: "failed"; readonly failure: Failure }
  | { readonly kind: "in"; readonly me: Me }
  /** The person signed out of the browser they are using, here. */
  | { readonly kind: "signed_out"; readonly everywhere: boolean }
  | { readonly kind: "deleted" };

const asBuilt = () => UNKNOWN;

/**
 * The page of an account: the searches that are kept, the last searches and the choice
 * of whether they are kept, where the person is signed in, a copy of everything Burro
 * holds, and deleting the account.
 *
 * It is built the same for everybody, and holds nothing of anybody until the browser has
 * asked the service. Whose account it shows is decided by the session, at the service:
 * the page sends no id of an account, and holds none.
 *
 * A search that was kept is opened in the search of the tab, which the session holds, so
 * that it is open on the search page the press leads to.
 *
 * What is pressed and then goes hands the focus to the heading of the page, which says
 * what became of the press.
 */
export function Account({ meta, areas, client = account, ranks = api }: Props) {
  return (
    // The search a kept search is opened in is the session's, as it is on the search page.
    <SessionBoundary>
      <SearchProvider meta={meta} areas={areas} client={ranks}>
        <Opened client={client} ranks={ranks} />
      </SearchProvider>
    </SessionBoundary>
  );
}

function Opened({ client, ranks }: { readonly client: AccountClient; readonly ranks: Client }) {
  const session = useSessionIfAny();
  const go = useGo();
  const [stage, setStage] = useState<Stage>({ kind: "opening" });
  const who = useSyncExternalStore(subscribeToWho, whoIs, asBuilt);
  const heading = useRef<HTMLHeadingElement>(null);
  // True once a press took away what was pressed: the heading then takes the focus.
  const handsOn = useRef(false);

  const load = useCallback(async () => {
    setStage({ kind: "opening" });
    const answer = await client.getMe();
    if (answer.ok) {
      noteSignedIn(answer.data.email);
      setStage({ kind: "in", me: answer.data });
      return;
    }
    const { failure } = answer;
    // A call that was stopped has nothing to report.
    if (failure.kind === "aborted") return;
    if (failure.kind === "api" && failure.code === NOT_SIGNED_IN) setStage({ kind: "out" });
    else setStage({ kind: "failed", failure });
  }, [client]);

  useEffect(() => {
    // Asked once, as the page opens: whose account it is, is the service's to say.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  // Before the page is drawn, so that the focus is never seen to be on nothing.
  useLayoutEffect(() => {
    if (!handsOn.current) return;
    handsOn.current = false;
    heading.current?.focus();
  }, [stage]);

  const open = useCallback(
    async (spec: PreferenceSpec): Promise<Failure | null> => {
      const held = session?.search() ?? null;
      if (held === null) return failed("unreadable").failure;
      const { failure } = await openKept(held, ranks, spec);
      if (failure === null) {
        // Nothing of the search before is left: not the areas that were chosen from it to
        // compare, as none is when a search is begun again.
        session?.compare.clear();
        // The search is open in the tab, and the search page draws it. What was pressed
        // goes with this page, so the search page is told to hand the focus on.
        noteOpened();
        go("search");
      }
      return failure;
    },
    [session, ranks, go],
  );

  // Whoever signs out, or deletes their account, leaves no search in the tab for whoever
  // sits down next: the page that says so leads to the search page, and a search says where
  // a person must get to. It is begun again, as "Start again" begins it, and the areas
  // that were chosen from it and the link that was made of it go with it.
  const letGoOfTheSearch = useCallback(() => {
    session?.compare.clear();
    session?.link.set(null);
    session?.search()?.flow.startAgain();
  }, [session]);

  // The service may say that somebody else is signed in than the page was opened for: they
  // signed in in another tab of this browser. What is drawn is then no longer theirs, and
  // whatever was pressed on it would be done to the account of the other.
  const another = stage.kind === "in" && who.kind === "in" && who.email !== stage.me.email;
  useEffect(() => {
    if (!another) return;
    // The page begins again, and asks the service whose account it is. What had the focus
    // goes with what was drawn, so the heading takes it.
    handsOn.current = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [another, load]);

  // An answer to anything may say that nobody is signed in: the session ended, or was ended elsewhere.
  const shown: Stage =
    stage.kind === "in" && who.kind === "out" ? { kind: "out" } : another ? { kind: "opening" } : stage;

  if (shown.kind === "in") {
    const { me } = shown;
    return (
      <Page>
        <Box title={ACCOUNT.title} rank={1} heading={heading}>
          {/* The address is the service's answer, and is drawn as words. */}
          <p className={parts.lead}>{ACCOUNT.as(me.email)}</p>
          <p>{ACCOUNT.lead}</p>
        </Box>
        <Searches client={client} open={open} />
        <Sessions
          client={client}
          onSignedOut={(everywhere) => {
            handsOn.current = true;
            setStage({ kind: "signed_out", everywhere });
            noteSignedOut();
            letGoOfTheSearch();
          }}
        />
        <Copy client={client} />
        <Remove
          client={client}
          fresh={me.fresh}
          onDeleted={() => {
            handsOn.current = true;
            setStage({ kind: "deleted" });
            noteSignedOut();
            letGoOfTheSearch();
          }}
        />
      </Page>
    );
  }

  const title =
    shown.kind === "out"
      ? ACCOUNT.out.title
      : shown.kind === "signed_out"
        ? ACCOUNT.signedOut.title
        : shown.kind === "deleted"
          ? ACCOUNT.remove.done.title
          : ACCOUNT.title;

  return (
    <Page lay="narrow">
      <Box title={title} rank={1} heading={heading}>
        {shown.kind === "opening" ? (
          <>
            <noscript>
              <p>{ACCOUNT.noScript}</p>
            </noscript>
            <p role="status" aria-live="polite">
              {ACCOUNT.opening}
            </p>
            <div aria-busy="true">
              <Skeleton lines={4} />
            </div>
          </>
        ) : null}

        {shown.kind === "out" ? (
          <>
            <p className={parts.lead}>{ACCOUNT.out.text}</p>
            <div className={parts.ways}>
              <Press kind="go" href={accountPaths.signIn()}>
                {ACCOUNT.out.signIn}
              </Press>
            </div>
          </>
        ) : null}

        {shown.kind === "failed" ? (
          <Failed title={ACCOUNT.failed} failure={shown.failure}>
            <Press
              kind="go"
              onPress={() => {
                // The button goes with the failure it stands in, and the focus must not go with it.
                handsOn.current = true;
                void load();
              }}
            >
              {ACCOUNT.tryAgain}
            </Press>
          </Failed>
        ) : null}

        {shown.kind === "signed_out" ? (
          <>
            <p className={parts.lead}>{shown.everywhere ? ACCOUNT.signedOut.everywhere : ACCOUNT.signedOut.text}</p>
            <div className={parts.ways}>
              <Press kind="go" href={paths.home()}>
                {ACCOUNT.signedOut.toSearch}
              </Press>
              <Press href={accountPaths.signIn()}>{ACCOUNT.signedOut.signIn}</Press>
            </div>
          </>
        ) : null}

        {shown.kind === "deleted" ? (
          <>
            <p className={parts.lead}>{ACCOUNT.remove.done.text}</p>
            <div className={parts.ways}>
              <Press kind="go" href={paths.home()}>
                {ACCOUNT.remove.done.toSearch}
              </Press>
            </div>
          </>
        ) : null}
      </Box>
    </Page>
  );
}
