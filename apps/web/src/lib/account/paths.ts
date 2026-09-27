/**
 * The addresses of the pages of accounts. Each is fixed: none takes an argument, so
 * nothing a person typed, no token and no id can be made into one.
 *
 * A link to sign in holds its token after the `#`, which a browser sends to no server.
 * The service makes that link. The website never builds one, and takes the token out of
 * the address as soon as it has read it.
 */

export const accountPaths = {
  /** Where a person asks for a link to sign in with. */
  signIn: () => "/sign-in",
  /** Where a person is told that a link was sent. */
  sent: () => "/sign-in/sent",
  /** The page a link opens. The token follows it, after the `#`. */
  confirm: () => "/sign-in/confirm",
  /** What a person keeps, and where they are signed in. */
  account: () => "/account",
} as const;

/** Every page of accounts, by its address. A page that is not among them is not one. */
export const ACCOUNT_PAGES: readonly string[] = Object.values(accountPaths).map((path) => path());
