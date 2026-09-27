/**
 * Site copy for accounts: signing in by a link sent by email, saving a search, and the page
 * of an account.
 *
 * It is written for somebody who has never seen Burro, and who is asked for their email
 * address: so it says what the address is for and what is kept, in whole sentences, before
 * it asks.
 *
 * But for the age a person must be, every figure here is the service's, and stands in a
 * gap: how long a link works for, how many searches an account may hold, a date. None is
 * written down here, so that a figure the service changes is never said wrongly. How long
 * a person stays signed in is said by the date the service gives, and by no sentence of
 * the website's. What the service refuses with is said in the service's own words, as
 * every failure is. Nothing here names a place.
 */

import type { Browser } from "@/lib/api/schema";

/**
 * What the website keeps in a browser, and what becomes of a search, where a person can
 * sign in. It is said on the page that the foot of every page calls "Privacy", in the place
 * of the line that says the website stores nothing in a browser, which is true only while
 * nobody can sign in. It names no figure: how long a link works, and how long a person
 * stays signed in, are the service's to say.
 */
export const KEPT_WITH_ACCOUNTS =
  "The website stores nothing in your browser unless you ask for a link to sign in. " +
  "When you do, it sets a cookie, which is a short piece of text that your browser keeps, " +
  "so that Burro can tell whether the link is opened in the browser that asked for it. " +
  "Once you have signed in, a second cookie keeps you signed in. " +
  "A search lives in memory, which means it is gone when you close the page, unless you are signed in and Burro keeps it for you.";

/** The one entry of the name board, which says where a person stands. */
export const ACCOUNT_NAV = {
  signIn: "Sign in",
  account: "Account",
} as const;

export const SIGN_IN = {
  pageTitle: "Sign in",
  pageDescription: "Sign in to Burro with a link that is sent to your email address.",
  title: "Sign in",
  lead:
    "When you are signed in, you can save a search and open it again later, on this device or on another one. " +
    "Burro has no passwords. Instead, it sends a link to your email address, and you sign in by opening that link.",
  field: "Your email address",
  /** What the address is for and what is kept of it, in a sentence each, beside the field that asks for it. */
  hint:
    "Burro uses this address to send you the sign-in link, and to know which account is yours. " +
    "It keeps the address with your account, and you can delete both whenever you like.",
  /** All that is kept, under the form, for whoever wants to know more before they give an address. */
  kept: {
    title: "What Burro keeps",
    points: [
      "The email is sent for Burro by a company that sends email, which is given your address so that the link can reach you.",
      "When you ask for a link, Burro notes which address it was for and when the link runs out. That is how a link comes to work once, and only for a short time.",
      "Once you have signed in, Burro keeps your address, the searches you save, the last few searches you made if you let it, and a record of when you signed in and with which kind of browser.",
      "Burro never keeps the words you type into a search. What it saves is what it understood from them, such as a budget or a vibe.",
      "You can see everything Burro holds on your account page. From there you can take a copy of it, and you can delete your account and all of it whenever you like.",
    ],
  },
  send: "Send me a link",
  sending: "Sending the link",
  /** The button was pressed on a field that holds nothing. */
  empty: "Type your email address in the box first, so that Burro knows where to send the link.",
  failed: "Burro could not send the link.",
  /**
   * Said to a person who has a search open in the tab, which is where the button that keeps
   * a search led them from: what they were doing is not lost.
   */
  stays:
    "Your search will stay open in this tab while you sign in. Keep the tab open, and come back to it afterwards to save your search.",
  /** Signing in is done by the page, and a browser with JavaScript off cannot do it. */
  noScript:
    "Signing in needs JavaScript, which is switched off in this browser. Switch it on and then load this page again.",
  /** Said in place of the form to a person who is signed in already. */
  already: (email: string) => `You are already signed in as ${email}.`,
  toAccount: "Go to your account",
} as const;

export const SENT = {
  pageTitle: "Check your email",
  pageDescription: "Says that a link to sign in was sent.",
  title: "Check your email",
  /** Said the same whether or not the address has an account. */
  to: (email: string) => `If ${email} can receive email, a sign-in link is on its way to it.`,
  /** The same, where the page no longer holds the address: it was loaded again, or opened another way. */
  toTheAddress: "If the address you gave can receive email, a sign-in link is on its way to it.",
  /** How long a link works for is the service's to say. */
  lasts: (minutes: number) =>
    minutes === 1
      ? "The link works once, and only for 1 minute, so open it as soon as it arrives."
      : `The link works once, and only for ${minutes} minutes, so open it as soon as it arrives.`,
  lastsAWhile: "The link works once, and only for a short time, so open it as soon as it arrives.",
  here:
    "If you can, open the link on this device and in this browser, because Burro then knows that whoever opens it is the person who asked for it. " +
    "If you open it somewhere else, Burro will ask you to confirm that it was you.",
  stays:
    "You can leave this page open while you do that. If you were in the middle of a search, " +
    "it will still be here when you come back to this tab, and you can save it then.",
  late:
    "If the email has not arrived after a few minutes, look in your junk folder. " +
    "If it is not there either, check the address and ask for another link.",
  again: "Ask for another link",
  back: "Back to the search",
} as const;

export const CONFIRM = {
  /** Its own, as the title of every page is: a person with both pages open tells them apart by it. */
  pageTitle: "Finish signing in",
  pageDescription: "Opens a link to sign in that was sent by email.",
  title: "Sign in to Burro",
  checking: "Burro is checking your sign-in link.",
  /** The page was opened another way than by a link. */
  none: {
    title: "This page opens from a sign-in link",
    text:
      "To sign in, open the link in the email that Burro sent you. " +
      "If you have not asked for a link yet, or your link has run out, you can ask for one now.",
  },
  /** What follows the address is no link that Burro makes. */
  notOne: {
    title: "This sign-in link is not complete",
    text:
      "Some of the link seems to have been lost, which can happen when a link is copied by hand or is broken across two lines of an email. " +
      "Open the link from the email again, or ask for a new one.",
  },
  ask: "Ask for a link",
  askAgain: "Ask for a new link",
  tryAgain: "Try again",
  /** The link is known, and the page says whose it is before anything is done with it. */
  ready: {
    lead: "This link will sign you in as:",
    check:
      "Check that this is your own email address before you go on. If it is somebody else's, close this page, " +
      "because signing in would put your searches into their account and not into yours.",
    /** The button says whom it signs in. It is pressed by a person, and by nothing else. */
    signIn: (email: string) => `Sign in as ${email}`,
  },
  /** The link was asked for in another browser than the one that holds it. */
  elsewhere: {
    title: "This link was asked for somewhere else",
    text:
      "Somebody asked for this link in a different browser, or on a different device, from the one you are using now. " +
      "That is as it should be if it was you, for example if you asked on a computer and opened the email on your phone. " +
      "If you did not ask for a sign-in link yourself, do not go on, because somebody may be trying to sign you in to an account that is theirs.",
    /** Asked a second time, once the button was pressed, with the address shown again. */
    again: "Do you want to sign in here?",
    as: "You would be signed in to the account of this address:",
    yes: (email: string) => `Yes, sign in as ${email}`,
    no: "No, do not sign in",
    /** Said once a person chose not to. */
    stopped: {
      title: "You have not been signed in",
      text: "Burro has not signed you in, and the link has not been used. You can close this page.",
      toSearch: "Go to the search",
    },
  },
  /** Signing in would make an account. */
  first: {
    text: "There is no Burro account for this address yet, so signing in will make one.",
    tick: "I am 18 or over",
    needed:
      "Burro's accounts are for people who are 18 or over. Tick the box to say that you are, and then press the button again.",
  },
  signingIn: "Signing you in",
  failed: "Burro could not sign you in.",
  couldNotCheck: "Burro could not check this link.",
  done: {
    title: "You are signed in",
    text: (email: string) => `You are now signed in as ${email} in this browser.`,
    /** How long that lasts is the service's to say, by a date, and the page of the account says it. */
    lasts: "Your account page says how long you will stay signed in here, and it is where you sign out.",
    made: "Burro has made an account for this address.",
    elsewhere:
      "If you were in the middle of a search in another tab, it is still open there. Go back to that tab to save it.",
    toSearch: "Go to the search",
    toAccount: "Go to your account",
  },
} as const;

export const ACCOUNT = {
  pageTitle: "Your account",
  pageDescription: "What Burro keeps for you, and where you are signed in.",
  title: "Your account",
  lead:
    "This page shows everything that you have asked Burro to keep for you. " +
    "From here you can open a search you saved, take a copy of what Burro holds, sign out, or delete your account.",
  opening: "Burro is opening your account.",
  /** The account is asked for by the page, and a browser with JavaScript off asks for nothing. */
  noScript:
    "Your account page needs JavaScript, which is switched off in this browser. Switch it on and then load this page again.",
  as: (email: string) => `You are signed in as ${email}.`,
  failed: "Burro could not open your account.",
  tryAgain: "Try again",
  /** Said in place of the page to a person who is not signed in. */
  out: {
    title: "You are not signed in",
    text: "Sign in to see the searches you have saved, and to look after your account.",
    signIn: "Sign in",
  },

  searches: {
    title: "Saved searches",
    /** How a search comes by its name, which is the service's to work out. */
    named:
      "Burro names each search from what it understood of it, such as its vibes and its budget, and never from the words you typed.",
    none:
      "You have not saved a search yet. To save one, make a search and then press Save this search, which stands under the first result.",
    count: (count: number, most: number) =>
      count === 1
        ? `You have saved 1 search. One account can hold ${most}.`
        : `You have saved ${count} searches. One account can hold ${most}.`,
    list: "Your saved searches",
    kept: (date: string) => `Saved on ${date}`,
    open: "Open",
    opening: "Opening",
    remove: "Remove",
    removing: "Removing",
    /** The whole name of a button, to whoever hears the page: what it does, and to which search. */
    of: (does: string, name: string) => `${does}: ${name}`,
    removed: "Burro has removed that search.",
    couldNotOpen: "Burro could not open this search.",
    couldNotRemove: "Burro could not remove this search.",
    couldNotList: "Burro could not list your saved searches.",
    /** Why a search cannot be opened, by what the service says of it. */
    state: {
      release_changed:
        "Burro's data has been brought up to date since you saved this search, and the search names something that the data no longer holds. Because of that, it cannot be opened as it is.",
      unreadable: "Burro can no longer read this search, which means it cannot be opened.",
    },
  },

  recent: {
    title: "Your last searches",
    keep: (most: number) => (most === 1 ? "Keep my last search" : `Keep my last ${most} searches`),
    hint:
      "While this box is ticked and you are signed in, Burro keeps each search you make, up to that number, " +
      "so that you can find one again without having saved it. It keeps what it understood of the search, and never the words you typed.",
    off: "Burro is not keeping your last searches, because the box above is not ticked.",
    none: "Burro has not kept a search for you yet. The next search you make while you are signed in will appear here.",
    list: "Your last searches",
    made: (date: string) => `Made on ${date}`,
    save: "Save",
    saving: "Saving",
    saved: "Burro has saved that search, so it now stands among your saved searches.",
    forget: "Forget my last searches",
    forgetting: "Forgetting",
    forgotten: "Burro has forgotten your last searches.",
    couldNotSet: "Burro could not change this setting.",
    couldNotList: "Burro could not list your last searches.",
    couldNotSave: "Burro could not save this search.",
    couldNotForget: "Burro could not forget your last searches.",
  },

  sessions: {
    title: "Where you are signed in",
    lead:
      "Each line is a browser in which you are signed in to Burro. If there is one that you do not recognise, sign out of it, " +
      "and whoever is using it will have to sign in again with a link sent to your email address.",
    list: "The browsers you are signed in with",
    /** The family of a browser, which is all the service keeps of what a browser says it is. */
    browser: {
      chrome: "Chrome",
      edge: "Edge",
      firefox: "Firefox",
      safari: "Safari",
      other: "Another browser",
    } satisfies Record<Browser, string>,
    here: "This is the browser you are using now.",
    made: (date: string) => `Signed in on ${date}`,
    seen: (date: string) => `Last used on ${date}`,
    ends: (date: string) => `Will be signed out on ${date} if it is not used before then`,
    signOut: "Sign out",
    signOutHere: "Sign out of this browser",
    signingOut: "Signing out",
    everywhere: "Sign out everywhere",
    everywhereHint: "Signing out everywhere signs you out of every browser at once, and this one is among them.",
    out: "Burro has signed that browser out.",
    couldNotList: "Burro could not list where you are signed in.",
    couldNotSignOut: "Burro could not sign you out.",
  },

  copy: {
    title: "A copy of what Burro holds",
    text:
      "You can save a copy of everything Burro holds about your account: your email address, the searches you saved, your last searches, " +
      "where you are signed in, and the record of what has happened to your account, such as each time a sign-in link was asked for. " +
      "The copy is a file in a format called JSON, which is plain text that other programs can read.",
    make: "Make a copy",
    making: "Making the copy",
    ready: "Your copy is ready. Press the link below to save it to your device.",
    save: "Save the copy",
    /** The name of the file, which holds nothing of the person. */
    file: "burro-account.json",
    failed: "Burro could not make the copy.",
  },

  remove: {
    title: "Delete your account",
    text:
      "Deleting your account removes everything Burro holds about it: your email address, the searches you saved, your last searches, " +
      "and the record of where you signed in. This cannot be undone.",
    shares:
      "A link to a search that you shared is no record of your account, because Burro does not keep who made a link. " +
      "This means that deleting your account does not remove those links.",
    ask: "Delete my account",
    sure: "Are you sure that you want to delete your account?",
    yes: "Yes, delete my account",
    no: "No, keep my account",
    deleting: "Deleting your account",
    failed: "Burro could not delete your account.",
    /** The person signed in too long ago for the service to delete the account at their word. */
    again:
      "Before it deletes an account, Burro asks you to sign in again. It asks for this so that nobody else can delete your account from a browser that you left signed in.",
    signIn: "Sign in again",
    done: {
      title: "Your account has been deleted",
      text: "Burro has deleted your account and everything that it held about it, and has signed you out.",
      toSearch: "Go to the search",
    },
  },

  /** Said once a person has signed out of the browser they are using. */
  signedOut: {
    title: "You have signed out",
    text: "You are signed out of Burro in this browser. What you saved is kept for you, and you will find it again when you next sign in.",
    everywhere: "You are signed out of Burro in every browser. What you saved is kept for you, and you will find it again when you next sign in.",
    toSearch: "Go to the search",
    signIn: "Sign in again",
  },
} as const;

/** The button on the search page that keeps a search. */
export const KEEP = {
  save: "Save this search",
  saving: "Saving this search",
  /** What the button says once the search on screen has been saved, until the search changes. */
  saved: "Search saved",
  done: "Burro has saved this search. You will find it on your account page, under Saved searches.",
  toAccount: "Go to your account",
  /** For a person who has not signed in, the button leads to signing in, and says so. */
  signIn: "Sign in to save this search",
  what: "Burro saves what it understood of your search, and never the words you typed.",
  failed: "Burro could not save this search.",
} as const;
