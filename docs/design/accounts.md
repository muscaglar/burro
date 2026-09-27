# Accounts: signing in, and what a person keeps

Status: built as groundwork on 2026-09-26, at the founder's asking, and **off until it is turned on**. The service and the website were each built against the contract. Run together on 2026-09-26, on a developer's own machine, they were walked in a browser: a link was asked for, read from the terminal, and opened, the page said whose it was, a press signed in, and the account was deleted from its page. **What was built was then tried hard, that day, on a copy on one machine and on no host.** Four things did not hold, and each was mended with a test that failed before it was: a page that the browser kept showed an account after its person had signed out, how long an answer took told that an address had asked for a link lately, a search that was taken away stayed in what is written beside the file, and ten requests from anybody stopped everybody from signing in where the website was not told which header names a client. This page says each where it belongs, as it now is. One thing was found that no page can mend, and section 4 says it at step 9. It applies ADRs [0043](../adr/0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md), [0044](../adr/0044-a-person-who-has-signed-in-may-keep-a-search-and-what-is-kept-is-the-spec-and-never-the-words.md) and [0045](../adr/0045-the-service-has-a-database-one-file-for-accounts-and-what-they-keep.md), and [0005](../adr/0005-raw-prompts-are-never-stored.md), [0011](../adr/0011-nothing-is-kept-for-a-search.md), [0023](../adr/0023-what-is-typed-goes-as-typed-and-people-are-told.md) and [0032](../adr/0032-calls-to-a-model-are-capped-for-the-whole-service.md) as each was amended for it. Nothing of it has run on a host.

This is the single source for accounts, in `services/api` and in `apps/web`. Where this document and the code disagree, one of the two is wrong, and is changed in the same commit. [What could go wrong](accounts-threats.md) says of each way in what holds it and what nothing holds: read it before you change anything here. [The guide to deployment](../../deploy/README.md#turning-accounts-on) says what the founder sets up, and [the privacy notice](../legal/privacy-notice.md), section 20, what people are told.

## 0. Terms

| Term | Meaning |
|---|---|
| Route N | The route with that number in section 6. Routes 1 to 14 are those of [the contract](contract.md), section 9.2 |
| The website | `apps/web`, as it runs at its host: the pages, and the handler that passes the routes of accounts on |
| The service | `services/api` |
| The file | The database: one file of SQLite (section 3) |
| A link | What a person is sent by email to sign in with. It holds a token |
| A token | 32 random bytes, as 43 characters of text. A link holds one, a session is one, and what binds a link to a browser is one |
| A spec | What Burro understood of a search: the `PreferenceSpec` of the contract, section 4. Never what was typed |
| Kept | Written to the file, under an account |

## 1. In short

| | |
|---|---|
| What an account is | An address of email, and what a person keeps under it. No name and no password |
| What it is for | Keeping a search, to open it again later, on this device or another |
| What needs one | Nothing that was there before. A search, a comparison, a share and the page of an area ask for none, and answer the same for everybody |
| How a person signs in | By a link sent to their address. The page a link opens says whom it would sign in, and signs nobody in until a button is pressed |
| What is kept of a search | The spec, the release it was made on, and a name worked out from the spec. Never the words |
| Where it is kept | One file of SQLite, on a volume of the machine that runs the service |
| What is logged | What happened and how it ended, each a word of a closed list. Nothing of a person |
| Whether it is on | No. One setting at the service and one at the website turn it on, and both are off unless they say `on` |

**What it changes of what Burro had promised in writing**, each amended in the change that built it:

| What was written | Where | What is so with accounts |
|---|---|---|
| The server keeps nothing for a search. A share is the only stored spec | [ADR 0011](../adr/0011-nothing-is-kept-for-a-search.md), `AGENTS.md` | A person who has signed in may keep a search, and may let Burro keep their last ten. It is kept because they asked, under their account, and they can take it away |
| "Burro builds no accounts, follows nobody, and keeps no store of what was typed" | [ADR 0023](../adr/0023-what-is-typed-goes-as-typed-and-people-are-told.md) | Burro builds accounts. It still follows nobody, and still keeps no store of what was typed |
| The service has no database | `AGENTS.md`, [the contract](contract.md) | It has one, a single file, for accounts and what they keep |
| The website sets no cookie, and has no handler of its own | [The design of the website](web.md), sections 2 and 10 | Two cookies, for a person who asks for a link and for nobody else. One handler, which passes a closed list of routes on |
| "The website stores nothing in your browser. A search lives in memory, which means it is gone when you close the page." | The page of methods, under "How your words are handled", which the foot of every page leads to by the word "Privacy" | Where accounts are on the page says what is then so, in the place of that line: that the website sets a cookie for a person who asks for a link and a second once they have signed in, and that a search is kept for a person who is signed in where Burro keeps it for them (`KEPT_WITH_ACCOUNTS` in `content/account.ts`, drawn by `MethodsTables`). With accounts off the page says the line as it was. *As accounts were first built the page said the one line whatever was set, so both of its sentences would have been untrue from the day accounts were turned on* |
| The service reads no address of a client | [ADR 0032](../adr/0032-calls-to-a-model-are-capped-for-the-whole-service.md) | It reads one on the routes of accounts, from the website alone, to count by. The cap on calls to a model is handed nothing, as before |

**What it does not change.** What a person types is never stored and never logged. No line of a log holds an address, a token, a session, the id of an account or of a search, the address of a client, a place, or a spec. Ranking is a pure function of a spec and a release, and is handed nothing of who asked. No dependency was added: what accounts need of a database, of randomness, of hashing and of HTTPS is in the standard library.

## 2. Off until it is turned on

One setting turns accounts on at the service, and one at the website. Each is off unless it says `on`.

| Where | Setting | What it may hold |
|---|---|---|
| The service | `BURRO_ACCOUNTS` | `on` or `off`, in any case. With nothing set, accounts are off. Any other word stops the service, which names the setting: left to mean off, a slip of the hand would leave accounts off and tell nobody |
| The website | `NEXT_PUBLIC_BURRO_ACCOUNTS` | `on`. Anything else, and nothing at all, leaves accounts off. It is read when the website is built, so a change does nothing until the next deployment. It is no secret: whether a person can sign in is plain from the name board |

**With accounts off, the website and the service are what they were before there were accounts.**

| Part | With accounts off | Held by |
|---|---|---|
| The routes of the service | None is served. Each answers 404 `not_found`, "Burro has nothing at this address.", as any address does that Burro has nothing at, and is logged as no route | `test_with_accounts_off_no_route_of_accounts_exists`, `test_with_accounts_off_a_route_of_accounts_is_logged_as_no_route` |
| The file | Is not opened, and none is made | `test_with_accounts_off_no_file_is_opened_and_nothing_of_them_is_made`, `test_starting_the_service_with_nothing_set_opens_no_file_of_accounts` |
| The other settings of accounts | Are not read, so one that is wrong cannot stop a service that has no accounts | `test_with_accounts_off_nothing_else_of_them_is_read_or_held` |
| The contract | Lists the routes all the same, because a client is made from it, and must be the same client wherever accounts are turned on | `test_the_contract_lists_the_routes_of_accounts_though_none_is_served` |
| The website's handler | Passes nothing on, and answers 404 with no body | `test_nothing_is_passed_on_and_the_answer_is_that_there_is_nothing_at_the_address` |
| The pages of accounts | None is built, and none is drawn when it is asked for: the address is answered as any address is that the website has nothing at, by the page that says so, whole. Each page stands in a folder that is built only where accounts are on (`pagesBuilt` in `lib/account/page.ts`), and `onlyWhereAccountsAreOn` is asked before a page draws anything. The settings of the website lead the address of each, and whatever follows it, to where no page stands, before any folder is asked (`ledNowhere` in `lib/account/off.ts`). *As it was first built `/sign-in/sent` and `/sign-in/confirm` were taken by the page of an area, which gave 404 with a frame that says nothing until scripts have run and that a cache may keep for an hour, and each asking for `/sign-in` or `/account` wrote a fault to the log of the website* | `test_no_page_is_built_at_the_address_and_none_is_drawn_when_it_is_asked_for`, `test_each_stands_in_a_folder_that_is_built_only_where_accounts_are_on`, `test_it_says_of_itself_what_a_page_that_is_not_there_says`, `test_the_address_of_every_page_of_accounts_and_whatever_follows_it_is_led_to_where_no_page_stands`, `test_the_settings_of_the_website_hold_the_rule_before_any_folder_is_asked`. What a built website answers is seen by asking one: no test does |
| The name board, and the search page | Draw no entry for an account, and no button that keeps a search. Neither asks the service anything | `test_it_holds_the_name_and_the_three_pages_and_nothing_of_accounts`, `test_nothing_is_drawn_and_nothing_is_asked`, `test_nothing_is_asked_of_the_service` |
| Cookies | None is set, and none is read | `test_with_accounts_off_the_service_is_what_it_was`, `test_a_search_knows_nobody_with_accounts_on_as_with_them_off` |
| What a browser is sent | The scripts of the website hold the code of accounts, which nothing draws and nothing asks with: one file of them holds "Send me a link", "Save this search" and `/v1/auth/link`. The framework's own list of the folders of the website stands in the markup of the page of an area, and names `sign-in` and `account` among them. No secret, no name of a header of the service and no setting of the server is in anything a browser is sent | No test holds what the framework writes. Seen in a build with accounts off, on 2026-09-26, and in a real browser: nothing of accounts was drawn, asked or kept |

**What must hold before accounts are turned on**, and what holds each:

| What | What holds it |
|---|---|
| A sender of email is named | With none named accounts are on, and asking for a link is answered 503 `sign_in_unavailable`. So nobody can sign in, and nobody is told that a link was sent. The sender that writes a link to the console is refused unless the service says that it is in development and listens to its own machine alone |
| The website is reached over TLS, at an origin that the service answers | `BURRO_ACCOUNTS_SITE` must begin `https://`, and be one of the origins of `BURRO_ALLOWED_ORIGINS`, to the letter. The service does not start otherwise |
| The website stands at a domain of Burro's own | **No code holds it.** A sender of email sends for a domain that is proved to be the sender's, so no mail is sent without one. [The guide to deployment](../../deploy/README.md#turning-accounts-on) says why a domain, and that nothing in the code asks that the service stands under the same one |
| The secrets are set | The service does not start where one is missing, is shorter than 32 characters, or where the two of its own are the same. It names the setting, and never what it was set to |
| The privacy notice says what is kept | **No code holds it.** It is a step of the founder's, in [the launch checklist](../legal/data-protection-checklist.md), under "Before accounts are turned on" |

**What the service says as it starts.** One line of the log, `accounts_on`, which holds nothing of how accounts are set. Where it cannot start it writes one line to standard error, and ends:

| It writes | It means |
|---|---|
| `error: accounts are on, and need these settings:` and the names of the settings | Each that is named is missing, or is not in the form it needs. Every one at fault is named at once, and what one was set to is never repeated |
| `error: the file of accounts could not be used [no_folder]` | The folder that `BURRO_ACCOUNTS_DB` names is not there. The service makes the file, and never a folder |
| The same, with `[not_permitted]` | The service may not write to the folder, or may not read and write the file. On a volume that was just made the folder is root's, and the service is not root. Nothing is made, and nothing is made the service's own. *As it was first built the service said `error: Permission denied` and no more, and of a file of its own in such a folder that it was no file of accounts* |
| The same, with `[not_a_file]` | What stands at that path is no file. *As it was first built a folder at that path was said in the words of the system, `error: Is a directory`* |
| The same, with `[open_to_others]` | The file was put there by hand, and others on the machine may read it. It is not made its owner's alone in silence: whoever put it there is told |
| The same, with `[not_a_file_of_accounts]` | What stands there is no file of SQLite that can be set as section 3 says |
| The same, with `[not_set]` | The file took a setting and did not keep it |
| The same, with `[layout_not_applied]` | A change to the layout failed, and was undone. The file is as it was |
| The same, with `[newer_layout]` | The file was made by a later build than this one. It is left as it was |

What the library says went wrong is let go of: it may name a value. A fault of the machine that is none of these ends the service with one line, `error:` and the fault in the words of the system, as `error: Too many levels of symbolic links`. Those words name no path and nothing of a person, and do not say that the fault is of accounts.

## 3. Where things are kept

SQLite, through the `sqlite3` module of Python's standard library: one file, on a volume of the host that is ciphered at rest and lasts from one deploy to the next ([ADR 0045](../adr/0045-the-service-has-a-database-one-file-for-accounts-and-what-they-keep.md)).

| Rule | Detail |
|---|---|
| One layer | `services/api/src/burro_api/accounts/store.py` holds the connection, and nothing else does. Every statement of accounts stands written in it, as a constant, and is a method of `Held`, which is the file held for one transaction |
| Every statement binds its values | None is made by putting strings together, by a format, or by joining. A test reads the module and fails on one that is built |
| Whose rows are read is said in the statement | A row of a search, a session, a preference or an event is found by its account, which the session gives and no request can. Two statements name no account, because each finds a session by the hash of its token, which is what says whose it is. Two more let go of what is too old, whoever it was of |
| How the file is set, each time it is opened | `journal_mode = WAL`, `foreign_keys = ON`, `busy_timeout = 5000`, `secure_delete = ON`, `trusted_schema = OFF`. The service reads each back, and does not start on a file that is not set so |
| What is deleted is written over | With `secure_delete`, the room of a row that is deleted is filled with noughts, and what was written ahead is brought into the file and its log cut to nothing. So an account that is deleted is gone from the file, and not only from its tables |
| What is taken away is gone from the file too | A search that a person takes away, the last searches that they have Burro forget or that go as they turn the keeping of them off, and the oldest of the last ten as an eleventh comes: after each, what was written ahead is brought into the file and its log cut to nothing, as after an account is deleted. *As it was first built such a search was out of the tables, and stayed in what is written ahead of the file, with the place its journey leads to, until an account was deleted or a day's links were let go of* |
| The file is its owner's alone | It is made readable and writable by the user the service runs as, and by nobody else. A file that is there already, and that others may read, is refused |
| One connection, behind a lock | A write is `BEGIN IMMEDIATE` to `COMMIT`, and what is written together is kept together or not at all. A read is of one moment |
| Every table is `STRICT` | A column takes no value of another kind. A word of a closed list is held to the list by the table itself |
| The layout has a version | The file holds it, as `user_version`. It is 1. A change is a list of statements that is added to `CHANGES` and never altered. Changes are applied as the file is opened, forward only, under a lock that lets nobody else read or write, and whole or not at all |
| A file of a later layout | Is refused, and left as it was: it was made by a later build, and may hold what this one cannot read |

The tables, as the first change makes them:

| Table | Column | What it holds |
|---|---|---|
| `accounts` | `id` | 128 random bits. It is in no answer and no log |
| | `email` | The address, made regular (section 4). One account an address |
| | `made_at`, `adult_at` | When the account was made, and when the person said that they are 18 or over |
| `login_tokens` | `token_hash` | The SHA-256 of the token of a link, and never the token |
| | `email` | The address the link was asked for, made regular. **It is held whether or not the address has an account** |
| | `made_at`, `ends_at`, `used_at` | When it was asked for, when it ends, and when it was used or ended by another |
| | `binding_hash` | The SHA-256 of what binds the link to the browser that asked |
| `sessions` | `token_hash` | The SHA-256 of the session, and never the session |
| | `public_id` | What a person names a session by, to sign out of it. It is not the session, and opens nothing |
| | `account_id` | Whose it is |
| | `made_at`, `seen_at`, `ends_at`, `revoked_at` | When it was made, when it was last put forward, when it ends, and when it was revoked |
| | `browser` | The family of the browser, coarsely: `chrome`, `edge`, `firefox`, `safari` or `other` |
| `saved_searches` | `id`, `account_id` | 128 random bits, and whose it is |
| | `spec` | The spec, as text |
| | `release_id` | The release it was made on |
| | `name` | What was understood, said in a line. Worked out from the spec, by the names the release gives: it holds the name of each place the journeys of the search lead to, and is the one column of the file, beside the spec, that says where somebody goes |
| | `made_at` | When it was kept |
| `recent_searches` | The same columns | The last ten of an account |
| `preferences` | `account_id`, `key`, `value` | A key of a closed list, which holds one: `keep_recent`. Its value is `on` or `off` |
| `audit_events` | `account_id`, `event`, `outcome`, `at` | What happened to an account, how it ended, and when (section 8) |

Every table that is of an account names it with `ON DELETE CASCADE`, so that to delete the row of an account is to delete everything of it.

**What is let go of, by its age.** No step runs by the clock: what is too old, of every kind, is let go of wherever accounts write already, by `let_go` in `accounts/service.py`, and what was written ahead is then brought into the file and its log cut to nothing. **So each period is the least, and not the most.** What is too old goes the next time anybody asks for a link or signs in, the next time a session is put forward, which is each day that somebody who is signed in comes back, and as the service starts. On a day when nobody does any of these it stays, and so it does while accounts are off, when the file is not opened. To hold a period to the day takes a step that runs by the clock, which is not built, and is the founder's to choose. *As it was first built each kind went only as a row of its own kind was written: with one account in use every day and nobody asking for a link, the address of somebody who had asked for a link and never signed in was still in the file 99 days on.* Each figure is a first guess, a constant of `accounts/service.py`, and the founder's to set.

| What | Let go of | When |
|---|---|---|
| A link | A day after it was asked for, used or not (`KEEP_LINKS`). With it goes the address it was asked for, where no account came of it | As the service starts, each time a link is asked for or somebody signs in, and each time a session is put forward |
| A session | 30 days after it ended or was revoked (`KEEP_SESSIONS`) | The same |
| What happened to an account | After 90 days (`KEEP_EVENTS`), and past the newest 200 of an account (`MOST_EVENTS`) | By its age, the same. Past the newest 200, each time something is kept of what happened |
| The last searches of an account | Past the newest ten (`MOST_RECENT`) | As one is added |
| An account, and a search that was kept | **Never by its age.** An account is kept until the person deletes it, and a search until they take it away | [The legal drafts](../legal/README.md), under "What accounts changed", set out the choice |

## 4. Signing in, by a link sent by email

Every rule of signing in is in `accounts/service.py`. A route hands on what was sent and serves what comes back.

| Step | What happens |
|---|---|
| 1. A person asks for a link | Route 15, with an address in the body. It is limited for each client first: ten in a quarter of an hour, or 429 `rate_limited` |
| 2. The address is made regular | It is put in lower case, and nothing else of it is changed: a full stop or a plus sign before the `@` is part of the address, because some hosts of mail read them as one mailbox and some as two. What is not in the shape of an address is refused, 422 `invalid_email`. So is an address that is not in plain letters: folded into plain letters it may be somebody else's (`accounts/addresses.py`) |
| 3. No account is looked for | So the work is the same whether or not the address has one, and so is the answer |
| 4. The limits of the address and of the service | In one transaction: three links to an address in a quarter of an hour, and ten in a day. 200 links from the whole service in an hour, unless `BURRO_ACCOUNTS_LINKS_PER_HOUR` says otherwise. They are counted in the file, by the rows of the links that were asked for. **An address over its limit is answered as every address is, 202, and as soon, and is sent nothing**: a refusal would say that somebody had asked for that address before, and so would an answer that came sooner. What is written to the file for it is what is written for any address, and is taken out again before it is kept. It leaves no row, so the hour counts it in the memory of the service, by its time and by nothing of its address. *As it was first built the hour counted rows alone: with the hour one short of full, whoever asked next was answered 429 where the address before had been sent an email and 202 where it had been over its limit.* The whole service over its cap answers 429 `sign_in_busy`, which says nothing of any address |
| 5. The token | 32 bytes from `secrets.token_urlsafe`, which is 43 characters. Its SHA-256 is kept, with the address, when it was asked for, when it ends, and the hash of what binds it to the browser. The token is kept nowhere |
| 6. The mail | **Sent once the answer has been given**, so that no answer waits on the company that sends, and none says by how long it took whether an email was sent. *As it was first built the email was sent before the answer: an address over its limit, which is sent none, was answered sooner by as long as the company takes, and whoever timed three answers could tell that a person had asked for a link in the last quarter of an hour.* It is sent to the address as it was made regular, which is the address an account bears, by the sender that is named. It is plain text, the same for everybody, and holds nothing that anybody typed. It says that the link works once and for 15 minutes, that the page will show whose link it is before it signs anybody in, that a person who did not ask may ignore it, and that the link is to be passed to nobody. `accounts/sender.py` has its words |
| 7. The link | `BURRO_ACCOUNTS_SITE`, then `/sign-in/confirm#t=`, then the token. The address of the website is the setting's, and never anything a request said. The token stands after the `#`, which a browser sends to no server |
| 8. The answer | 202, with how many minutes a link lasts, and a cookie, `__Host-burro_link`, which lasts as long and holds a second token: what binds the link to this browser. Where the browser held one already, the links it asked for before are bound to the new one |
| 9. The page a link opens | Reads the token from the address, takes it out of the address bar at once, and holds it in memory alone (`lib/account/token.ts`). It sends no referrer, as no page of the website does. **What this does not reach**: a browser keeps the address a page was opened at, whole, in its record of how the page was loaded, where a script of the page itself can read it until the page is left. No page can take it out, and no other site can read it. The token there is a quarter of an hour old at the most, and works once |
| 10. The page asks whose link it is | Route 16, with the token in a body. It reads, and writes nothing, so it uses nothing up. It answers with the address, with whether the link was asked for in this browser, and with whether signing in would make an account |
| 11. The page says whom it would sign in | "This link will sign you in as:", the address, and a button that bears the address. Where the link was asked for in another browser the page says so first, shows the address again, and asks a second time. Where signing in would make an account it asks the person to tick that they are 18 or over |
| 12. A press sends the token | Route 17, with `adult` where the box was ticked and `other_browser` where the person was asked the second time. **Nothing but a press calls it** |
| 13. The session is made | In one transaction: the link is found by the hash of its token, which is compared in constant time. That it has not ended and was not used is checked. A link from another browser is refused, 409 `other_browser`, unless the request says that the person was asked. An address with no account is refused, 409 `age_not_confirmed`, unless the box was ticked. Then the account is made if there was none, **every link of the address is ended**, the session that the browser came with is revoked if it came with one, and a new session is made |
| 14. The answer | The address, whether an account was made, and the cookie of the session. The cookie that bound the link is taken back |

| A link that opens nothing | Is answered |
|---|---|
| What is not in the shape of a token, or is the token of no link that is held | 422 `link_not_valid` |
| A link that was used, or that another of its address ended | 410 `link_used` |
| A link that is older than 15 minutes | 410 `link_expired` |

A client may show a link thirty times in a quarter of an hour, to routes 16 and 17 together, or is answered 429 `rate_limited`. It is no part of the design, and it is no guard against guessing, which a token of 256 bits needs none of: it bounds the work that one client can ask for.

**Sending.** One small interface, `Sender`, with one method. The sender is named by `BURRO_ACCOUNTS_SENDER`:

| Named | What it does |
|---|---|
| Nothing | No sender. Asking for a link is answered 503 `sign_in_unavailable` |
| `postmark`, `resend` | One call over HTTPS with the standard library, to a host and a path that are written in the code and are no setting. The key goes in one header, and shows in no `repr`. The body of no answer is read: a refusal can repeat the address it refuses. To Postmark the mail says of itself that no link of it is to be followed and that it is not to be counted when it is opened. Resend has no such field in a mail: it is a setting of the domain, at the company. **Neither has been run against its company** |
| `console` | Writes the address and the link to standard error, and sends nothing. The log is written to standard output, so no line of the log holds a link in development either. It is refused unless `BURRO_ACCOUNTS_DEVELOPMENT` is `yes` and `BURRO_HOST` is the loopback address |

| Where the sender fails | The person is answered | The log says |
|---|---|---|
| The company could not be used at all: its key is refused, it is over a limit of its own, it is at fault, or it did not answer | 202, as every address is: the answer was given before the email was sent, so it cannot say that the email failed. **Whoever asks for a link in the minute after is answered 503 `sign_in_unavailable`**, whatever their address (`DOWN_FOR`) | `link_send_failed`, `unavailable`, and for whoever asks after, `link_requested`, `unavailable` |
| The company was reached, and would not take this mail | 202, as every address is. What it would not take may be about the address, so nobody who asks after is told of it | `link_send_failed`, `refused` |

A link that was not sent is ended, and is still counted among those of its address. So one person a minute may be told that a link is on its way where the company cannot be reached, and it is not. The minute is a first guess, and the founder's to set.

**What the minute tells.** An address over its limit hands the company no email, so nothing fails for it. While the company cannot be used, the answer to whoever asks next therefore says whether the ask before it handed the company an email, and so whether its address was over its limit: 503 where it was not, 202 where it was. By counting asks of their own for an address, whoever wants to know can count those that somebody else made for it, within the day. It is when a person who got no email asks again and again. One line closes it, `DOWN_FOR = timedelta(0)`: nobody is then told that the company cannot be reached, and everybody who asks meanwhile is told that a link is on its way. Seven tests lean on the minute, and are turned with it. To set the minute from what the last email came to was tried and closes less: the answers still differ as the company stops, and then differ as it starts again. **The choice is the founder's.**

## 5. A session, and the website between

| The cookie | `__Host-burro_session` |
|---|---|
| How it is set | `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/`, and no `Domain`. The prefix `__Host-` is one a browser takes only from the host itself, over TLS, for the whole of the host |
| What it holds | 32 random bytes. The file holds their SHA-256 |
| How long it lasts | 30 days. It is put forward to 30 days from now when it is used, once a day at the most, and never past 90 days from when it was made. The cookie is given again as it is put forward |
| A new one is always made | Signing in makes a session, and revokes the one the browser came with. No route takes a session from a body or an address |
| In development | The website is in the clear on a machine of one's own, where a browser need take neither the prefix nor `Secure`. There, and nowhere else, the two cookies bear their plain names, `burro_session` and `burro_link`, and are not `Secure`. Chrome, tried on 2026-09-26, took neither the prefix nor `Secure` from a page at `http://127.0.0.1`, and took both from one at `http://localhost`. No other browser was tried. The service names them so only where `BURRO_ACCOUNTS_DEVELOPMENT` is `yes`, and the website lets them by only where its own `BURRO_ACCOUNTS_DEVELOPMENT` is `yes` and the request reached it in the clear at `127.0.0.1`, `localhost` or `[::1]`. Out of development a cookie under a plain name opens nothing and binds nothing |

**The website stands between the browser and the service for these routes.** A browser asks `/v1/auth/*` and `/v1/me/*` of the website's own origin, and the website passes each on (`apps/web/src/lib/account/pass.ts`, behind the handlers under `apps/web/src/app/v1/`). So the cookie is the website's own, and no browser sends it across sites.

| What the website does | Detail |
|---|---|
| Passes on a closed list of routes | The seventeen of section 6, each held to its method and its path whole and to the letter (`lib/account/routes.ts`). The address that is asked of the service is the route of the list, and never the path as it was sent. Anything else answers 404 |
| Passes nothing on that has a query | A request with anything after a `?` answers 404 |
| Refuses what changes something and did not come from a page | 403, unless the request bears `X-Burro-Request: 1` and `Content-Type: application/json`, and the browser says that it came from the same origin, or says nothing of where it came from |
| Passes on a closed list of headers | `Accept`, `Content-Type`, `Origin`, `User-Agent` and `X-Burro-Request`. Of cookies, the two of accounts and no other |
| Says who it is | By `X-Burro-Website`, which holds the secret of `BURRO_WEBSITE_SECRET`. It is sent to the service and to nobody else, and never to a browser. A secret shorter than 32 characters is taken for none |
| Reaches the service over TLS | What is passed on holds the secret, the cookie of a session and the body of the request. So where the address of the service does not begin `https://` the website passes nothing on, and answers 503: as the service does not start with a website in the clear. Only on a machine of one's own, where the website is being developed and was itself reached in the clear, is the service reached in the clear. *As it was first built the website asked that there was an address of the service, and not how it was reached* |
| Says what the address of the client is, with every request it passes on | In `X-Burro-Client-Address`, from the header that `BURRO_CLIENT_ADDRESS_HEADER` names, which is the one the website's host gives it in, and must be one that the host writes over whatever a client sent under its name. **Where the host gave no one address the website passes nothing on**, and answers 503: no header is named, the header holds none, or it holds two, a list, or what is no address. Only on a machine of one's own, where no host stands before the website, is a request passed on with no address. A header named `X-Burro-Client-Address` that a client sent is never passed on, because no header is passed on that is not of the list |
| Holds a body to 16 KiB | As the service does. A larger one is answered 413 |
| Passes back a closed list of headers | `Content-Type`, `Retry-After`, `X-Burro-Preview`, `X-Burro-Synthetic` and `X-Request-Id`, and a cookie only where it is one of the two and is set as the first table says |
| Says of every answer that it may not be kept | `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`, on what it passes back and on what it refuses itself |
| Follows nothing | An answer that leads elsewhere, or that is not JSON, is not the service's, and is answered 502 |
| Writes nothing down | No line of a log and nothing to the console. What it refuses it refuses with a status and no body, so that nothing that was sent is repeated |

| The website answers, with no body | Where |
|---|---|
| 404 | Accounts are off, the request is for no route of the list, or it has a query |
| 403 | It changes something and did not come from a page of the website |
| 413 | Its body is larger than 16 KiB |
| 503 | The website was not given the address of the service or its secret, the address does not begin `https://`, or it cannot say whose the request is: `BURRO_CLIENT_ADDRESS_HEADER` names no header, or what is no name of one, or the host gave no one address in the header it names |
| 502, 504 | The service was out of reach or did not answer as itself, or did not answer in 20 seconds |

**The service hears the website, and nobody else** (`accounts/gate.py`, and `heard` in `accounts/service.py`). The gate stands before anything is made of what was sent: nothing is made of a body that anybody else sent, and it never reaches a route. The edge of the service has counted its bytes by then, and no more.

| What is asked of a request | Or it is answered |
|---|---|
| `X-Burro-Website` once, and the same as the secret. The two are hashed and then compared in constant time, so that not even the length of the secret is told | 403 `not_the_website` |
| No query | 422 `invalid_request` |
| Of a request that is no `GET`: `Content-Type: application/json` | 415 `unsupported_media_type` |
| Of the same: one `Origin`, which is one of `BURRO_ALLOWED_ORIGINS`, exactly, and `X-Burro-Request: 1` once. Two of either are nothing a browser sends | 403 `not_the_website` |
| `X-Burro-Client-Address` once, with one address in it that can be read | 403 `not_the_website`. The website gives one address with every request, so what holds two, or none, or what is no address, is not what the website wrote. Only in development is a request heard that names none |

**The address of a client** is what that header holds, made regular: an address of the older kind as it is, and one of the newer kind as the network of 64 bits it is in, because a client that is given addresses of the newer kind is given a network of them. **No client is counted with the unknown.** A request that names no address, or one that cannot be read, is refused, so that the limits count people: *as it was first built those of whom nothing was said were counted together as one client, and with the setting of the website left unset, which no guide then spoke of, ten requests from anybody stopped everybody from signing in for a quarter of an hour*. Only in development, where no host stands before the website, are they counted together. **An address is counted, and kept nowhere.** A count is held in the memory of the process under a hash made with `BURRO_ACCOUNTS_LIMITS_KEY`, for a quarter of an hour, for 100,000 clients at the most. It is in no table, no line and no file, and it starts again when the service does (`accounts/limits.py`).

**A `GET` changes nothing that a person keeps.** The one thing it writes is when a session was last used and when it ends, where a day has passed since the session was last put forward: that is how a session lasts. With that write, and with no other of a `GET`, what is too old is let go of (section 3). Every route that changes anything takes what it is about in a body.

| Signing out | What it does |
|---|---|
| Route 19 | Revokes the session at the service, and takes the cookie back whether or not it opened anything. A cookie that was kept opens nothing after |
| Route 30, with the id of a session | Signs out of that browser. The id is what a session is named by in route 29, and is not the session |
| Route 30, with `everywhere` | Revokes every session of the account, the one that asked among them |

## 6. The routes

Routes 15 to 31, in `services/api/src/burro_api/routes/accounts.py`. Each is under `/v1/auth` or `/v1/me`. None takes anything in its path or in a query. `contracts/openapi.json` has each record field by field, and the records are in `accounts/wire.py`. In the contract each is marked `accounts`, so that a client that is made from it can tell them from the routes it asks of the service itself: a browser asks these of the website.

| # | Route | Takes | `data` | Errors of its own | Changes anything |
|---|---|---|---|---|---|
| 15 | `POST /v1/auth/link` | `email` | 202. `lasts_minutes`. The same whoever asked and whatever the address. Sets the cookie that binds the link | 422 `invalid_email`, 429 `rate_limited`, 429 `sign_in_busy`, 503 `sign_in_unavailable` | Yes |
| 16 | `POST /v1/auth/link/whose` | `token` | `email`, `same_browser`, `new_account` | 422 `link_not_valid`, 410 `link_used`, 410 `link_expired`, 429 `rate_limited` | **No.** It is a `POST` so that the token travels in a body |
| 17 | `POST /v1/auth/session` | `token`, `adult`, `other_browser` | `email`, `new_account`. Sets the cookie of the session | As route 16, and 409 `other_browser`, 409 `age_not_confirmed` | Yes |
| 18 | `GET /v1/auth/session` | | `signed_in`, and `email` or `null`. It is answered 200 either way | | No |
| 19 | `DELETE /v1/auth/session` | | `signed_in` false | | Yes |
| 20 | `GET /v1/me` | | `email`, `made_at`, `preferences`, and `fresh`: whether the person signed in within the last ten minutes | 401 `not_signed_in` | No |
| 21 | `DELETE /v1/me` | | `signed_in` false | 401 `not_signed_in`, 403 `sign_in_again` | Yes |
| 22 | `POST /v1/me/searches` | `spec` | The search as it is kept: `search_id`, `name`, `spec`, `release_id`, `kept_at`, `state` | 401, 409 `too_many_searches`, 422 `invalid_spec` and what route 2 refuses a spec with | Yes |
| 23 | `GET /v1/me/searches` | | `searches`, the newest first, and `most`, which is 100 | 401 | No |
| 24 | `DELETE /v1/me/searches` | `search_id` | The searches that are left | 401, 404 `search_not_found` | Yes |
| 25 | `POST /v1/me/recent` | `spec` | `kept`, `searches`, and `most`, which is 10 | 401, and what route 22 refuses a spec with | Yes, where the person lets Burro keep them. Where they do not, nothing is kept, and `kept` is false |
| 26 | `GET /v1/me/recent` | | The same | 401 | No |
| 27 | `DELETE /v1/me/recent` | | The same, with none | 401 | Yes |
| 28 | `PUT /v1/me/preferences` | `keep_recent`: `on` or `off`. Left out, or `null`, it stays as it was | Every preference as it now stands: what the person chose, or what stands for a person who has chosen nothing | 401 | Yes. To turn the last searches off is to delete them |
| 29 | `GET /v1/me/sessions` | | `sessions`: those that have not ended and were not revoked, the newest first, each with `session_id`, `browser`, `made_at`, `seen_at`, `ends_at`, `current` and `revoked`. And `signed_in`, which is whether the browser that asked still is | 401 | No |
| 30 | `DELETE /v1/me/sessions` | `session_id`, or `everywhere` | The sessions that are left, and whether the browser that asked is still signed in | 401, 404 `session_not_found`, 422 `invalid_request` where both are sent or neither | Yes |
| 31 | `GET /v1/me/export` | | Everything Burro holds of the account (section 7) | 401 | No |

Every route can also answer 403 `not_the_website`, 422 `invalid_request` and 500 `internal_error`. One that is no `GET` can answer 413 `body_too_large` and 415 `unsupported_media_type`, and one that takes a body 400 `malformed_json`.

| Rule | Detail |
|---|---|
| The envelope | As every route's: `meta`, with the two flags of the release, and `data` or `error`. A message is fixed text for its code, is written for a person who has never seen Burro, and never repeats what was sent |
| Who is signed in | Is decided by the session, at the service, in `accounts/gate.py`, and by nothing else that was sent. No route takes the id of an account, or an address, but route 15 |
| An id of somebody else's | Finds nothing and changes nothing. It is answered as an id of nobody's: 404, with the same words |
| A spec | Is a `PreferenceSpec`, the record the ranking takes. It is checked by `check_spec` against the release that is served before it is kept, and again when it is read |
| `seen_at` of a session | Is put forward once a day at the most, so it says the day and little more |
| Every answer | Carries `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`, a refusal among them. The edge of the service sets both for every route of accounts, whatever the route itself said |
| The contract | Keeps the version it had. The routes were added, and no route that was there changed, so accounts ask for no new version |

## 7. What is kept of a search

| What is kept | Detail |
|---|---|
| The spec | As text: `PreferenceSpec.model_dump_json()`. It is what the reducer left, and holds no word that was typed: its every field is a number, a word of a closed list, or an id of the release |
| The places of it | As the person named them, by their ids. A share makes them coarse, because anybody may open it. A kept search is shown to the person who kept it, and to nobody else |
| The release it was made on | Its id |
| A name | Worked out from the spec, and from the names the release gives, by `name_of` in `accounts/names.py`, when the search is kept. "Renting a 1-bedroom home, up to £1,700 a month, about 35 minutes to Cindermoor Works by public transport, Leafy, Quiet streets". A search that asks for nothing is "Renting, with what Burro counts in every search", which is what the website calls what nobody chose. Every kind of search has a word of its own, "Renting", "Buying" or "Visiting": a visit holds no budget and no kind of home, so its name has neither. A usual setting that nobody chose is not named. A person cannot type a name |
| The same search | Is kept once, however often it is pressed. Among the last ten, a search that is made again comes to the top, and is not held twice |
| How many | A hundred that were kept, and the last ten. The hundred-and-first is refused, 409 `too_many_searches`. The eleventh takes the place of the oldest |

**A name holds what the spec holds.** It names a place that a person must reach, and what they can pay. So it is handled as a spec is: it is in the file and in an answer, and in no log.

**When a search is read, it is checked again**, by the schema and against the release that is served that day, and is served with a `state`:

| `state` | What is so | What the website does |
|---|---|---|
| `ok` | The spec can be ranked on the release that is served | Opens it: the spec is loaded into the search that is open in the tab and ranked now, as the spec of a shared link is (`lib/account/open.ts`) |
| `release_changed` | It names a place, an area or a measure that the release no longer holds | Says that the data has been brought up to date since, and that the search cannot be opened as it is. It is not mended |
| `unreadable` | What is kept can no longer be read as a search. `spec` is `null` | Says that Burro can no longer read it |

**The last searches are built two ways, and one line chooses.** The line is `KEEP_RECENT` in `accounts/settings.py`, and the setting `BURRO_ACCOUNTS_KEEP_RECENT` says the same without a change to the code.

| Way | Setting | What is so |
|---|---|---|
| Kept once a person turns it on. **The code is left on this one** | `asked`, which is so with nothing set | Nothing of a search is kept until a person presses to keep it, or ticks the box of their account that lets Burro keep their last searches |
| Kept from the start | `from_the_start` | The last searches of a person are kept from their first sign-in, until they untick the box |

Either way it is what stands for a person who has chosen neither. Whoever has ticked the box or unticked it is kept to what they chose, and to untick it is to delete what was kept.

**Which search is a last search.** The website sends a search to route 25 once its ranking has stood on the page for five seconds, because a setting that is moved ranks again at every step, and what is kept is what the person stopped at. It sends it only where somebody is signed in, where the service has said that they let Burro keep their last searches, and where the search is their own: one that came from a link somebody shared is not. Whether they let Burro keep them is asked of the service again as the person who is signed in changes, since what was learned of one person is not held of the next (`lib/account/who.ts`). *As it was first built it was asked once for a tab: a search of the next person to sign in was sent where they had let nothing be kept, and was not sent where they had.* The service keeps it only where the person lets it, whatever the website sent.

**A search is a person's own where they were signed in as it was made.** The search of a tab outlasts whoever made it: it stands until the tab is closed, while one person signs out and another signs in. So the website holds, beside the ranking that stands, that somebody was signed in as the search page first saw it, and that nobody has taken their place since. It holds nothing of who they are (`lib/account/recent.ts`). What somebody else made, and what anybody made who was not signed in, is sent to be kept by nothing but a press of "Save this search", by whoever is signed in and reads it on the page. A person who was not signed in was told that a search is gone as the page is closed, so theirs is kept for nobody who signs in after them. *As it stood on 2026-09-27, once whether the last searches are kept was asked again of each person, the search that stood in a tab was sent to be kept for whoever signed in next, where they let Burro keep their last searches. Tried in a browser: the search of one person, with the place they must get to, was kept in the account of another, who had made no search and pressed nothing.* The service cannot hold this: it keeps what it is sent for whoever the session says, and cannot tell whose a search was. What the button says of a search that was saved, or that could not be, is said to the person who pressed, and to nobody who signs in after them: their account holds no such search.

**Why the code is left on `asked`.** It keeps nothing that a person did not ask to have kept, which is what [the privacy notice](../legal/privacy-notice.md) has said of Burro from the start. The founder asked that previous searches be stored and shown again, and with `asked` a person who never finds the box never sees theirs. [ADR 0044](../adr/0044-a-person-who-has-signed-in-may-keep-a-search-and-what-is-kept-is-the-spec-and-never-the-words.md) has what each way costs. **The choice is the founder's.**

**The copy of an account**, route 31, holds everything that the file holds of it, read at one moment:

| Field | What it holds |
|---|---|
| `exported_at` | When the copy was made |
| `email`, `made_at`, `adult_at` | The address, when the account was made, and when the person said that they are 18 or over |
| `preferences` | Each as it stands |
| `searches`, `recent` | Every search that is kept, and the last ten, each as routes 23 and 26 serve it |
| `sessions` | Every session that is held, those that ended or were revoked among them |
| `events` | What happened to the account (section 8) |
| `links` | Each link that was asked for the address, for as long as it is held: when it was asked for, when it ends, and whether it was used. Never the link |

It holds no id of the account, no hash, and nothing of anybody else.

**Deleting an account**, route 21, asks that the person signed in within the last ten minutes, or answers 403 `sign_in_again`. It deletes the row of the account, and with it every session, search, preference and event of it, and every link that was asked for its address, in one transaction. What was deleted is then written over in the file (section 3). A link that was shared is no record of an account, and is not deleted with one: nothing says who made it.

## 8. What is logged, and what is kept to look back on

**The log keeps its closed list of what a line may hold** ([the contract](contract.md), section 10.1). For accounts `LOGGABLE` gained two fields, `happened` and `outcome`. Each holds a word of a closed list, which is the value of an enum in `accounts/events.py`.

| `happened` | What happened |
|---|---|
| `link_requested` | A link was asked for |
| `link_sent` | The sender took the mail |
| `link_send_failed` | It did not |
| `link_used` | A link signed somebody in |
| `link_rejected` | A link was shown, and opened nothing |
| `session_created` | Somebody signed in |
| `session_revoked` | Somebody signed out, or a session was revoked as another was made |
| `rate_limited` | A limit was reached |
| `account_deleted` | An account was deleted |

| `outcome` | How it ended |
|---|---|
| `ok` | As it was meant to |
| `refused` | It was turned away: an address that is no address, a link that Burro does not know, a link from another browser or an age that was not confirmed, a mail the company would not take |
| `expired` | The link was older than 15 minutes |
| `used` | The link had been used, or ended |
| `limited` | A limit was reached |
| `unavailable` | No sender is named, or the sender could not be used |

| Line | Holds | Written |
|---|---|---|
| `account` | `request_id`, `happened`, `outcome`, and the time | Once for each thing that happens. One request may write two or three |
| `accounts_on` | Nothing | Once, as the service starts with accounts on |
| `request` | What it holds for any route: the template of the route, the status, the code of an error, and how long it took | Once for each request |

**No line holds an address, a token, a session, the id of an account, of a session or of a search, the address of a client, or a spec.** No field of the list could hold one. `request_id` is made by the service for each request and says nothing of who asked: it ties the lines of one request together, and no two requests.

**What happened to an account is kept with the account**, in `audit_events`: the same two words, and when. It is kept in the transaction that did the thing. A person reads it in the copy of their account, and it goes when the account goes.

| What is kept of an account | What is not |
|---|---|
| A link of its address that was used | A link that was asked for. No account is looked for when one is, so nothing is kept of it under an account: the link itself is held for a day, by its address |
| A session that was made, and one that was revoked | A link that was shown and opened nothing. It is logged, and not kept with the account it was for: what is kept of an account is so many rows, and whoever held a link that had ended could show it until every row was of that, and none of who had signed in |
| | That the account was deleted. There is then no account to keep it under, and the log says it |
| | Who did it, and from where |

## 9. Hardening

| What | Detail |
|---|---|
| No answer of these routes is kept by a browser, or by anything between | `Cache-Control: no-store`, set at the edge of the service for every route of accounts and again by the website |
| No answer is taken for what it does not say it is | `X-Content-Type-Options: nosniff`, the same |
| The list of origins stays exact | No pattern and no "every origin". No answer carries `Access-Control-Allow-Credentials`, so no cookie is ever allowed across origins |
| A browser that asks first what it may send is told what it was always told | `GET`, `POST` and `Content-Type`, and nothing of accounts. So no page of another origin may send the header of a page, a `PUT` or a `DELETE`: the browser itself refuses. A browser asks the routes of accounts of the website's own origin, where it asks nothing first |
| A failure is the service's own envelope | It never repeats what it was sent. The website's own refusals have no body at all |
| A body is held to 16 KiB | At the website and at the service |
| Nothing is followed | The service answers with no redirect, and the website follows none |
| The secrets come from the environment | `BURRO_WEBSITE_SECRET`, `BURRO_ACCOUNTS_LIMITS_KEY` and `BURRO_ACCOUNTS_SENDER_KEY`. Each is needed as the service starts where it is used, is held as a secret that shows in no `repr`, no dump and no line, and is in no file of the repository |
| One secret is not used for two things | The service refuses to start where the secret of the website and the key of the limits are the same |
| A hash is compared in constant time | With `hmac.compare_digest`, and with no `==` before it that would tell first |
| The file is its owner's alone, and what is deleted from it is written over | Section 3 |
| Nothing the file itself says is run as code | `trusted_schema = OFF` |
| The page of the website lets nothing else draw it | `frame-ancestors 'none'`, in the policy the website had already. The policy did not change for accounts |

## 10. The website

| Path | Page | What it does |
|---|---|---|
| `/sign-in` | Sign in | Says what an account is for, asks for an address, and says beside the field what the address is used for and what is kept of it. Under the form it lists all that is kept. It sends route 15, and then leads to the next page |
| `/sign-in/sent` | Check your email | Says that a link is on its way if the address can receive email, in the same words whatever the address. It says how long a link lasts, as the service said, and asks the person to open it in this browser if they can |
| `/sign-in/confirm` | The page a link opens | Section 4, steps 9 to 14 |
| `/account` | Your account | The address, the searches that are kept, the last searches with the box that lets Burro keep them, where the person is signed in, a copy of what Burro holds, and deleting the account |

| Part | Where | What it does |
|---|---|---|
| The entry of the name board | Every page | "Sign in", or "Account" for a person who is signed in. Drawn only where accounts are on. **On a screen narrower than 40rem it is built two ways, and one line chooses**: `ENTRY_ON_A_NARROW_SCREEN` in `components/AccountEntry/look.ts`. With `gives-way`, which the code is left on, the entry is not drawn in the board once a search is open, so that the board stays one line and the first result stands where it stood, and the way to signing in and to the account stands after the first result, with the button that keeps a search. With `stays` it is in the board in every state. **What each way costs was measured again on 2026-09-26, of the board as it stands**, because the board holds three pages since that evening and held four while the entry was built. In a window 844 high, after a plain search: on a phone 360 wide or wider the entry stands on the one line of the board, which is 52 px high with it and without it, and the first result stands from 452 to 838 at 390 wide either way. On a phone 320 wide the entry takes a second line, the board is 96 px high where it is 52, and the first result begins at 630 where it began at 586. The choice is the founder's |
| The button that keeps a search | The search page, beside the way to share a search, after the first result | "Save this search". For a person who has not signed in it is a link to signing in, and says so. The search they were making is still open in the tab when they come back |

| Rule | Detail |
|---|---|
| The website keeps nothing in the storage of a browser | As before. The one thing a browser holds of an account is the two cookies, which no script can read |
| Who is signed in is asked of the service | The page asks route 18 as it opens. It asks again when a person comes back to the tab they asked for a link in, since a link is most often opened in another, and when somebody who is signed in comes back to the tab: they may have signed out since, in another tab, or of every browser from another one. What it holds is the address, in memory (`lib/account/who.ts`) |
| A page that was opened for one person begins again where another is signed in | The page of an account hears who is signed in, as every part of the website does. Where the service says that it is somebody else than the page was opened for, because they signed in in another tab of the browser, the page begins again: it asks whose account it is and draws that, and whatever it had drawn of the first person goes (`components/Account/Account.tsx`). *As it was first built it went on naming the first person, and a press on it was done to the account of the second.* A press that is made before the page has been told is not reached |
| What a page holds of an account is let go of as the browser puts the page away | A browser keeps a page that a person has left, as it stood, and shows it again when they press Back. It asks nothing as it does. So as a page is put away it lets go of who is signed in, of the address a link was asked for, of the token of a link, and of everything of an account that it has drawn. When it is shown again it begins again, and asks the service (`lib/account/away.ts`). *As it was first built a person signed out, somebody pressed Back, and the page of their account was shown as it had stood, with their address and the searches they had kept.* Whoever presses Back to the page a link opened must open the link from the mail once more |
| The search of the tab is let go of as a person leaves | As a person signs out of the browser they are using, signs out everywhere or deletes their account, on the page of their account, the search that is open in the tab is begun again, and the areas that were chosen from it and the link that was made of it go with it (`components/Account/Account.tsx`). The page that says so leads to the search page, where whoever sits down next would read where the person must get to. It is done once the service has answered. *As it was first built the search stayed, and was kept among the last searches of the next person to sign in in that tab.* A search in another tab is not reached, and nor is the search of a tab whose session was ended from elsewhere |
| The address a link was asked for | Is held in memory while the page is open, so that the next page can say where the link went. It is in no address of a page and in nothing the browser keeps. Once the page is loaded again it says "the address you gave" (`lib/account/asked.ts`) |
| The token | Is read from the address once, taken out of it, and held in memory. What is not in the shape of a token is never sent anywhere and never shown |
| Where a page leads by itself | To a page of a closed list, by its name, which takes no argument (`lib/account/go.ts`). Nothing that was sent says where a person goes after they sign in |
| The pages of accounts | Are built the same for everybody, hold nothing of anybody, and are never indexed: each says so in its own markup, and in a header. An address with anything after that of a page is answered as one the website has nothing at, and no page of accounts is drawn at it. **With accounts on it is not answered whole where it is of two parts**, as `/account/x` is: the page of an area takes it, as it takes every address of two parts that no page stands at, and answers 404 in a frame that says nothing until scripts have run. The framework writes `NoFallbackError` to the log of the website as it turns such an address away from a page of accounts. Seen on a build with accounts on, on 2026-09-27. The rule that holds the addresses with accounts off (section 2) holds nothing with accounts on, so that no address a person signs in by is ever weighed against a rule. What an address of two parts is answered with is the page of an area's to mend, for every such address at once |
| The copy | Is made in the page from the answer of route 31, and saved by the person as `burro-account.json`. The name of the file holds nothing of them |
| Signing in needs scripts | The page says so where they are off |
| The content security policy | Did not change. The routes of accounts are asked of the website's own origin, which the policy allowed already |
| The words | Are in `apps/web/src/content/account.ts`, written as [the guide to the words](words.md) asks. But for the age a person must be, every figure in them is the service's: how long a link lasts, how many searches an account holds, a date |

## 11. The settings, by name

The service reads each once, as it starts, and only where `BURRO_ACCOUNTS` is `on` (`accounts/settings.py`). A setting that is missing, or is not in the form it needs, stops the service, which names the setting and never what it was set to: a value in the wrong setting could be a secret.

| Setting of the service | What it is for | What it may hold | With nothing set |
|---|---|---|---|
| `BURRO_ACCOUNTS` | Turns accounts on | `on`, `off` | Off |
| `BURRO_ACCOUNTS_DB` | The file accounts are kept in | A path, in a folder that is there | The service does not start |
| `BURRO_ACCOUNTS_SITE` | The origin of the website: where a link leads, and where a page asks from | An origin that begins `https://` and is one of `BURRO_ALLOWED_ORIGINS`. `http://` only in development, on the loopback address | The service does not start |
| `BURRO_WEBSITE_SECRET` | **A secret.** What the website is known by | 32 to 512 characters of plain letters, digits and marks, with no space | The service does not start |
| `BURRO_ACCOUNTS_LIMITS_KEY` | **A secret.** What the addresses of clients are counted under | The same. It may not be the same as the secret of the website | The service does not start |
| `BURRO_ACCOUNTS_SENDER` | Who sends a link | `postmark`, `resend`, or `console` in development | No sender: asking for a link is answered 503 |
| `BURRO_ACCOUNTS_SENDER_KEY` | **A secret.** The key of the company that sends | 1 to 512 characters, with no space | The service does not start where a company is named. A key with no company named is let go of |
| `BURRO_ACCOUNTS_SENDER_FROM` | The address a link is sent from | A plain address, in lower case, with no name before it | The same |
| `BURRO_ACCOUNTS_LINKS_PER_HOUR` | How many links the whole service sends in an hour | A whole number from 0 to 10,000. Nought sends none | 200. A first guess, and the founder's to confirm |
| `BURRO_ACCOUNTS_KEEP_RECENT` | Whether a person's last searches are kept from the start | `asked`, `from_the_start` | `asked` |
| `BURRO_ACCOUNTS_DEVELOPMENT` | That the service is being developed, on a machine that listens to itself alone | `yes`, `no` | `no`. `yes` is refused unless `BURRO_HOST` is the loopback address |

| Setting of the website | What it is for | What it may hold | With nothing set |
|---|---|---|---|
| `NEXT_PUBLIC_BURRO_ACCOUNTS` | Turns accounts on. Read when the website is built | `on` | Off |
| `BURRO_WEBSITE_SECRET` | **A secret.** The same as the service's. Read on the server alone | 32 characters at the least | The handler answers 503, and passes nothing on |
| `BURRO_CLIENT_ADDRESS_HEADER` | The name of the header in which the website's host gives the address of a client. It must be one that the host writes over, whatever a client sent under its name: at Vercel `x-vercel-forwarded-for`, as its page was read, which nobody has tried | The name of a header | **Nothing is passed on, and every route of accounts answers 503**, but on a machine of one's own in development. So does what is no name of a header |
| `NEXT_PUBLIC_BURRO_API_URL` | Where the service is, as before | For the routes of accounts, an address that begins `https://`, but on a machine of one's own | The handler answers 503 |
| `BURRO_ACCOUNTS_DEVELOPMENT` | That the website is being developed. It changes two things, and only for a request that reached the website in the clear on the machine it runs on: the two cookies are let by under their plain names, and a request is passed on though no host said whose it is | `yes` | It is not. **Never set it at a host** |

**The numbers that are no setting** are constants of `accounts/service.py`, and each is the founder's to change:

| Constant | Is | What it holds |
|---|---|---|
| `LINK_LASTS_MINUTES` | 15 | How long a link works for |
| `LINKS_TO_AN_ADDRESS` | 3 in a quarter of an hour, 10 in a day | How many links one address is sent |
| `LINKS_FROM_A_CLIENT` | 10 in a quarter of an hour | How often one client may ask for a link |
| `SHOWN_BY_A_CLIENT` | 30 in a quarter of an hour | How often one client may show a link |
| `SESSION_LASTS`, `PUT_FORWARD_AFTER`, `SESSION_AT_MOST` | 30 days, 1 day, 90 days | How long a session lasts, how often it is put forward, and the most it lasts in all |
| `FRESH_FOR` | 10 minutes | How lately a person must have signed in to delete their account |
| `MOST_SEARCHES`, `MOST_RECENT` | 100, 10 | How many searches an account keeps |
| `KEEP_LINKS`, `KEEP_SESSIONS`, `KEEP_EVENTS`, `MOST_EVENTS` | 1 day, 30 days, 90 days, 200 | What is let go of by its age (section 3) |
| `DOWN_FOR` | 1 minute | How long nobody is sent a link once the company that sends was out of reach |

## 12. What is tested

Every rule above has its test. A test is named for what it protects, and the name is given here so that it can be searched for. `make ci` runs those of the service, and `make web-check` those of the website.

**The service**, under `services/api/tests/accounts/`:

| What is held | Test | In |
|---|---|---|
| With accounts off no route of them exists, and a route that is asked for is logged as no route | `test_with_accounts_off_no_route_of_accounts_exists`, `test_with_accounts_off_a_route_of_accounts_is_logged_as_no_route` | `test_off.py` |
| With accounts off no file is opened, and the service is what it was | `test_with_accounts_off_no_file_is_opened_and_nothing_of_them_is_made`, `test_with_accounts_off_the_service_is_what_it_was`, `test_starting_the_service_with_nothing_set_opens_no_file_of_accounts` | `test_start.py` |
| The contract is the same with accounts on as with them off | `test_the_contract_is_the_same_with_accounts_on_as_with_them_off`, `test_the_contract_lists_the_routes_of_accounts_though_none_is_served` | `test_start.py`, `test_off.py` |
| A search knows nobody, with accounts on as with them off | `test_a_search_knows_nobody_with_accounts_on_as_with_them_off`, `test_an_answer_of_the_search_is_as_it_was` | `test_me.py`, `test_gate.py` |
| One setting turns accounts on, and what they need is needed at start and named where it is missing | `test_accounts_are_off_unless_the_one_setting_says_on`, `test_what_accounts_need_is_needed_at_start_and_is_named_where_it_is_missing`, `test_every_setting_that_is_missing_is_named_at_once`, `test_the_command_line_names_what_accounts_need_and_never_what_was_set` | `test_settings.py`, `test_start.py` |
| A secret is shown in nothing, and one secret is not used for two things | `test_a_secret_is_held_and_is_shown_in_nothing`, `test_a_secret_that_is_too_short_or_cannot_go_in_a_header_is_refused`, `test_one_secret_is_not_used_for_two_things` | `test_settings.py` |
| What development allows is allowed on a machine that listens to itself alone | `test_the_service_is_in_development_only_where_it_listens_to_this_machine_alone`, `test_a_link_is_never_to_a_website_in_the_clear_but_in_development`, `test_the_sender_for_development_is_refused_where_the_service_is_not_in_development`, `test_out_of_development_the_service_does_not_start_with_what_development_allows` | `test_settings.py`, `test_start.py` |
| A request without the website's secret is refused, before anything is made of what it sent | `test_a_request_without_the_websites_secret_is_refused`, `test_a_secret_that_is_not_the_websites_is_refused`, `test_what_a_stranger_sends_is_refused_before_it_is_read` | `test_gate.py` |
| What changes anything needs an origin of the list, JSON, and the header of a page, and signing in needs all three though there is no cookie yet | `test_what_changes_anything_comes_from_a_page_of_the_website`, `test_what_changes_anything_says_that_a_page_of_burro_asked`, `test_what_changes_anything_is_sent_as_json_and_as_nothing_a_form_can_send`, `test_asking_for_a_link_needs_all_three_though_there_is_no_cookie_yet`, `test_an_origin_that_is_sent_twice_is_no_origin_of_a_page` | `test_gate.py` |
| A `GET` changes nothing, and uses no token up | `test_a_get_needs_the_website_and_no_more_and_changes_nothing`, `test_a_get_uses_no_token_up` | `test_gate.py`, `test_sign_in.py` |
| No route takes a query, and no id is in a path | `test_no_route_takes_a_query`, `test_no_route_takes_typed_text_in_a_path_or_query` | `test_gate.py`, `tests/test_contract.py` |
| A header of a client's address that a client sent is not believed | `test_an_address_that_a_client_wrote_is_not_believed`, `test_the_header_of_an_address_is_believed_from_the_website_alone`, `test_two_addresses_say_that_the_website_did_not_write_them_alone` | `test_gate.py` |
| A request of the website's that does not say whose it is is refused, and no client is counted with the unknown but in development | `test_a_request_that_does_not_say_whose_it_is_is_not_the_websites`, `test_no_client_is_counted_with_the_unknown_but_in_development` | `test_gate.py` |
| What is held of a client is a hash under a key, and never the address | `test_what_is_held_of_a_client_is_a_hash_under_a_key_and_never_the_address`, `test_under_another_key_the_same_address_is_held_as_something_else` | `test_limits.py` |
| Every answer is never kept, and no cookie is let across origins | `test_every_answer_is_never_kept_and_is_what_it_says_it_is`, `test_no_browser_is_let_send_a_cookie_or_the_header_of_a_page_across_origins` | `test_gate.py` |
| An address is put in lower case and nothing else of it is changed, and one that is not in plain letters is refused | `test_an_address_is_put_in_lower_case_and_nothing_else_of_it_is_changed`, `test_a_full_stop_and_a_plus_are_part_of_an_address`, `test_an_address_that_is_not_in_plain_letters_is_refused_and_never_folded` | `test_addresses.py` |
| A token is 32 bytes from the system's own source, and what is kept of one is its hash | `test_a_token_is_32_bytes_from_the_systems_own_source`, `test_what_is_kept_of_a_token_is_its_sha_256_and_never_the_token`, `test_what_is_kept_of_a_link_is_the_hash_of_its_token_and_never_the_token` | `test_tokens.py`, `test_sign_in.py` |
| A token, a session and the secret are each compared in constant time | `test_a_token_a_session_and_the_secret_are_each_compared_in_constant_time`, `test_two_hashes_are_compared_in_a_time_that_does_not_tell_how_alike_they_are`, `test_a_secret_is_compared_by_its_hash_so_that_not_even_its_length_is_told` | `test_sign_in.py`, `test_tokens.py` |
| A link is sent to the address made regular, and leads where the setting says | `test_asking_for_a_link_sends_one_to_the_address_made_regular` | `test_sign_in.py` |
| An address that is known and one that is not get the same answer, the same work, and like time | `test_a_known_address_and_an_unknown_one_are_answered_the_same`, `test_a_known_address_and_an_unknown_one_are_given_the_same_work`, `test_a_known_address_and_an_unknown_one_are_answered_in_like_time` | `test_sign_in.py` |
| An email is sent once the answer has been given, and an address over its limit is answered as soon as any other, is given the same work, and leaves nothing in the file | `test_a_letter_is_sent_once_the_answer_has_been_given`, `test_an_address_over_its_limit_is_answered_as_soon_as_one_that_is_sent_a_letter`, `test_an_address_over_its_limit_is_given_the_same_work_as_any_other`, `test_what_is_written_for_an_address_over_its_limit_is_in_no_byte_that_is_left` | `test_sign_in.py` |
| A link works once, ends after a quarter of an hour, and ends every other of its address as it is used | `test_a_link_works_once`, `test_a_link_ends_after_a_quarter_of_an_hour`, `test_using_a_link_ends_every_other_that_was_asked_for_the_same_address`, `test_of_two_that_use_one_link_at_once_one_signs_in` | `test_sign_in.py` |
| A link that is opened in another browser is not taken without being asked, and a link that somebody else sent signs nobody in unseen | `test_a_link_opened_in_another_browser_is_not_taken_without_being_asked`, `test_a_link_that_somebody_else_sent_signs_nobody_in_unseen`, `test_a_browser_binds_no_link_but_its_own`, `test_a_cookie_under_the_plain_name_binds_nothing` | `test_sign_in.py` |
| The first sign-in makes the account, once the person says that they are an adult | `test_the_first_sign_in_makes_the_account_once_the_person_says_they_are_an_adult`, `test_a_person_who_has_an_account_is_not_asked_their_age_again` | `test_sign_in.py` |
| A session is never taken from the client, and its cookie is set as the design says | `test_a_session_is_never_taken_from_the_client`, `test_signing_in_again_makes_a_new_session_and_revokes_the_one_the_browser_had`, `test_signing_in_gives_the_session_and_takes_back_what_bound_the_link`, `test_the_hash_of_a_session_opens_nothing` | `test_sign_in.py`, `test_sessions.py` |
| A session lasts 30 days, is put forward once a day at the most, and never lasts past 90 | `test_a_session_lasts_thirty_days`, `test_a_session_is_put_forward_when_it_is_used_once_a_day_at_the_most`, `test_a_session_never_lasts_past_ninety_days_from_when_it_was_made` | `test_sessions.py` |
| Signing out revokes the session at the service, and signing out everywhere revokes every session of the account and no other | `test_signing_out_revokes_the_session_at_the_service`, `test_signing_out_everywhere_revokes_every_session_of_the_account_and_no_other`, `test_a_session_of_somebody_elses_is_not_found_and_is_not_ended` | `test_sessions.py` |
| What is kept of a browser is its family, and what it says it is is written nowhere | `test_what_is_kept_of_a_browser_is_its_family_and_nothing_else`, `test_what_a_browser_says_it_is_is_written_nowhere` | `test_sessions.py` |
| The limits: three and ten to an address, ten from a client, so many from the whole service | `test_three_links_to_an_address_in_a_quarter_of_an_hour_and_no_more`, `test_ten_links_to_an_address_in_a_day_and_no_more`, `test_ten_requests_from_one_client_in_a_quarter_of_an_hour_and_no_more`, `test_the_whole_service_sends_so_many_links_in_an_hour_and_no_more`, `test_a_client_may_show_so_many_links_in_a_quarter_of_an_hour_and_no_more` | `test_sign_in.py` |
| An address over its limit fills the hour as any other, so that a full hour does not say which it was | `test_an_address_over_its_limit_fills_the_hour_as_any_other` | `test_sign_in.py` |
| With no sender named signing in answers that it cannot, a sender that cannot be reached is said to whoever asks next, and a mail that the sender will not take is answered as any other | `test_with_no_sender_named_signing_in_answers_that_it_cannot`, `test_a_sender_that_cannot_be_reached_is_said_to_whoever_asks_next`, `test_a_letter_the_sender_will_not_take_is_answered_as_any_other` | `test_sign_in.py` |
| The mail is plain text, the same for everybody, and is not followed or counted | `test_the_letter_is_plain_text_and_the_same_for_everybody`, `test_the_letter_is_written_for_a_person_who_has_never_seen_burro`, `test_a_letter_is_not_followed_and_is_not_opened_for_the_sender`, `test_nothing_the_company_answers_is_read` | `test_sender.py` |
| No statement is made by putting strings together, every one binds its values, and one layer touches the connection | `test_no_statement_is_ever_made_by_putting_strings_together`, `test_every_statement_that_takes_a_value_binds_it`, `test_one_layer_is_the_only_code_that_touches_the_connection`, `test_what_is_sent_as_a_value_is_kept_as_a_value_and_runs_nothing` | `test_store.py` |
| The file is its owner's alone and is set as the design says. A layout of a later version is refused | `test_the_file_is_made_for_its_owner_alone_and_is_set_as_the_design_says`, `test_the_layout_holds_the_seven_tables_and_each_holds_its_columns_to_their_kind`, `test_a_file_of_a_later_layout_is_refused_and_is_left_as_it_was`, `test_a_change_to_the_layout_that_fails_leaves_the_file_as_it_was`, `test_a_change_to_the_layout_is_applied_under_a_lock_and_whole` | `test_store.py` |
| A file that cannot be used is refused in a word of the store's own, which the service says as it ends, and is left as it was | `test_a_folder_that_is_not_there_is_said_and_nothing_is_made`, `test_what_the_service_may_not_write_to_is_said_in_a_word_of_the_stores_own`, `test_a_folder_where_the_file_should_be_is_said_to_be_no_file`, `test_a_file_that_others_may_open_is_refused`, `test_a_file_that_is_no_file_of_accounts_is_refused_and_is_left_as_it_was`, `test_the_command_line_says_that_the_file_of_accounts_cannot_be_used`, `test_the_command_line_says_that_the_file_of_accounts_may_not_be_written_to` | `test_store.py`, `test_start.py` |
| Every look-up names the account, and no route under `/v1/me` ever returns a row of another account, tried with many accounts and with ids that are guessed | `test_every_look_up_of_what_is_kept_names_the_account`, `test_no_route_ever_returns_a_row_of_another_account`, `test_an_id_that_is_guessed_or_is_somebody_elses_gives_nothing`, `test_whose_rows_are_read_is_never_decided_by_what_a_request_says` | `test_store.py`, `test_me.py` |
| What is kept of a search is what Burro understood, named from it, and holds no word that anybody typed | `test_a_search_is_kept_as_what_burro_understood_and_named_from_it`, `test_what_is_kept_holds_no_word_that_anybody_typed` | `test_me.py`, `test_names.py` |
| A search of every kind can be kept, a visit among them, and each kind has a word of its own | `test_every_kind_of_search_has_a_word_of_its_own`, `test_a_visit_is_named_as_one_and_has_no_home_and_no_budget_to_name`, `test_a_search_that_is_a_visit_is_kept_named_and_shown_again` | `test_names.py`, `test_me.py` |
| A spec is checked by the schema the ranking uses before it is kept, and again when it is read | `test_a_search_is_checked_by_the_schema_the_ranking_uses_before_it_is_kept`, `test_a_search_that_names_what_the_data_does_not_hold_is_not_kept`, `test_a_search_is_checked_again_when_it_is_read`, `test_a_search_kept_on_other_data_says_whether_it_can_be_searched_now` | `test_me.py` |
| A hundred searches at the most, the last ten, and the same search once | `test_a_hundred_searches_are_kept_at_the_most`, `test_the_last_ten_are_kept_and_the_oldest_goes`, `test_the_same_search_is_kept_once_however_often_it_is_pressed` | `test_me.py` |
| The last searches are kept only once a person turns it on, and the other way from the start | `test_the_last_searches_are_kept_only_once_a_person_turns_it_on`, `test_the_other_way_the_last_searches_are_kept_from_the_start`, `test_turning_it_off_takes_away_what_was_kept` | `test_me.py` |
| A preference is a key from a closed list, with a value checked for it | `test_a_preference_is_a_key_from_a_closed_list_with_a_value_checked_for_it`, `test_a_preference_that_is_not_on_the_list_cannot_be_kept` | `test_me.py`, `test_store.py` |
| A person is given everything Burro holds of them | `test_a_person_is_given_everything_burro_holds_of_them`, `test_every_row_the_file_holds_of_an_account_is_in_what_the_person_is_given` | `test_me.py` |
| An account is deleted with everything of it, after a sign-in in the last ten minutes, and what is deleted is gone from the file | `test_an_account_is_deleted_with_everything_of_it_in_the_file_and_beside_it`, `test_deleting_asks_for_a_sign_in_in_the_last_ten_minutes`, `test_putting_a_session_forward_does_not_make_it_a_fresh_sign_in`, `test_what_is_deleted_is_gone_from_the_file_and_not_only_from_the_tables` | `test_me.py`, `test_store.py` |
| What a person takes away is gone from the file, and from what is written beside it | `test_a_search_that_is_taken_away_is_gone_from_the_file_and_from_beside_it`, `test_last_searches_that_are_taken_away_are_gone_from_the_file_and_from_beside_it`, `test_turning_it_off_takes_what_was_kept_out_of_the_file_and_from_beside_it`, `test_the_oldest_of_the_last_searches_is_gone_from_the_file_as_it_goes` | `test_me.py` |
| What is too old is let go of | `test_a_link_is_let_go_of_after_a_day_whoever_asked_for_it`, `test_links_that_are_too_old_are_let_go_of_as_the_service_starts`, `test_sessions_that_ended_long_ago_are_let_go_of_as_a_person_signs_in`, `test_what_happened_to_an_account_is_cut_to_so_many_and_let_go_of_by_its_age` | `test_sign_in.py`, `test_sessions.py`, `test_store.py` |
| What is too old goes of every kind, wherever accounts write, and not only as a row of its own kind is written | `test_an_address_that_never_signed_in_goes_as_somebody_who_is_signed_in_comes_back`, `test_what_is_too_old_of_every_kind_is_let_go_of_as_a_link_is_asked_for`, `test_what_is_too_old_of_every_kind_is_let_go_of_as_the_service_starts`, `test_a_session_that_ended_long_ago_is_let_go_of_as_somebody_else_comes_back`, `test_what_happened_long_ago_is_let_go_of_as_somebody_else_comes_back` | `test_sign_in.py`, `test_sessions.py` |
| No line of the log holds an address, a token, a session, an account, the address of a client or a spec, or anything in the shape of one | `test_no_line_holds_an_address_a_token_a_session_an_account_a_client_or_a_spec`, `test_the_log_gained_two_fields_and_each_is_a_word_of_a_closed_list`, `test_a_line_of_accounts_holds_what_happened_and_how_it_ended_and_no_more`, `test_a_failure_in_accounts_is_logged_by_its_type_and_answered_in_fixed_words` | `test_log.py` |
| What is kept of what happened is of the two lists, and of an account. A link that is refused is not kept with one | `test_what_is_kept_of_what_happened_is_of_the_two_lists_and_of_an_account`, `test_an_event_that_is_not_on_the_list_cannot_be_kept`, `test_a_link_that_has_ended_cannot_be_shown_until_nothing_else_is_kept` | `test_log.py`, `test_store.py`, `test_me.py` |

**The website**, under `apps/web/`. A component's test stands beside it, in `src/components/`:

| What is held | Test | In |
|---|---|---|
| With accounts off nothing is passed on, no page of accounts is reached, and nothing of them is drawn or asked | `test_nothing_is_passed_on_and_the_answer_is_that_there_is_nothing_at_the_address`, `test_they_are_off_unless_the_one_setting_says_on`, `test_no_page_is_built_at_the_address_and_none_is_drawn_when_it_is_asked_for`, `test_nothing_is_drawn_and_nothing_is_asked` | `src/lib/account/pass.test.ts`, `test/account/pages.test.tsx`, `KeepSearch.test.tsx` |
| With accounts off the address of every page of accounts, and whatever follows it, is led to where no page stands, by the settings of the website. With accounts on no address is led anywhere | `test_the_address_of_every_page_of_accounts_and_whatever_follows_it_is_led_to_where_no_page_stands`, `test_no_page_stands_where_they_are_led_and_no_folder_takes_an_address_of_one_part`, `test_the_settings_of_the_website_hold_the_rule_before_any_folder_is_asked`, `test_no_address_is_led_anywhere` | `src/lib/account/off.test.ts` |
| The page that the foot calls "Privacy" says what a browser keeps as it is set: nothing of a cookie with accounts off, and the two cookies and a search that is kept with them on | `test_where_nobody_can_sign_in_the_page_says_nothing_of_a_cookie_or_of_signing_in`, `test_where_a_person_can_sign_in_the_page_says_what_the_browser_and_burro_then_keep` | `MethodsTables.test.tsx` |
| The website has one handler, which passes accounts on, and no action or middleware | `test_the_website_has_one_handler_which_passes_accounts_on_and_no_action_or_middleware`, `test_the_website_has_two_routes_and_both_pass_the_routes_of_accounts_on` | `test/privacy/source.test.ts`, `test/account/route.test.ts` |
| What is passed on is a closed list of routes, of headers and of cookies | `test_every_route_of_the_list_is_passed_to_the_same_route_of_the_service`, `test_a_request_with_anything_after_a_question_mark_is_passed_nowhere`, `test_only_the_headers_of_the_list_are_passed_on`, `test_only_the_two_cookies_of_accounts_are_passed_on`, `test_only_the_headers_of_the_list_are_passed_back` | `pass.test.ts` |
| The secret reaches the service and is in nothing a browser is served | `test_the_secret_reaches_the_service_and_is_in_nothing_a_browser_is_served`, `test_a_secret_that_a_client_sent_is_not_passed_on_in_the_place_of_the_websites_own` | `pass.test.ts` |
| Nothing is passed on to a service that is reached in the clear, but on a machine of one's own | `test_a_service_that_is_reached_in_the_clear_%s_is_passed_nothing`, `test_on_a_machine_of_ones_own_the_service_is_reached_in_the_clear_as_the_website_is` | `pass.test.ts` |
| The address of a client is what the website's host says, and never what a client said | `test_it_is_what_the_websites_host_says_and_never_what_a_client_said`, `test_one_address_is_passed_on_as_the_host_gave_it`, `test_with_the_header_of_the_host_named_wrongly_nothing_is_passed_on` | `pass.test.ts` |
| Nothing is passed on where the website's host gave no one address of a client, but on a machine of one's own | `test_with_no_header_of_the_host_named_nothing_is_passed_on`, `test_where_the_host_gave_what_is_no_one_address_nothing_is_passed_on`, `test_where_the_host_gave_none_nothing_is_passed_on_whatever_a_client_said`, `test_anywhere_else_a_request_with_no_address_is_passed_nowhere`, `test_on_a_machine_of_ones_own_a_request_is_passed_on_with_no_address`, `test_with_accounts_on_and_nothing_said_of_whose_request_it_is_nothing_is_passed_on` | `pass.test.ts`, `test/account/route.test.ts` |
| A cookie is let by only where it is one of the two and is set as it must be | `test_a_cookie_the_service_sets_is_let_by_where_it_is_one_of_the_two_and_is_set_as_it_must_be` | `pass.test.ts` |
| Every answer says that no browser may keep it, and nothing is written to the console | `test_every_answer_of_the_route_says_that_no_browser_may_keep_it`, `test_nothing_is_written_to_the_console_whatever_becomes_of_a_request` | `pass.test.ts` |
| The token is taken out of the address bar at once, goes in a body, and is nowhere else | `test_it_is_taken_out_of_the_address_bar_at_once_and_before_anything_is_asked`, `test_it_is_put_in_the_place_of_the_entry_that_held_it_and_no_entry_is_added`, `test_it_goes_to_the_service_in_the_body_of_a_request_and_in_no_address`, `test_it_is_nowhere_on_the_page_in_no_attribute_and_in_nothing_the_browser_keeps` | `Confirm.test.tsx` |
| The page says whose link it is, and signs nobody in until the button is pressed | `test_the_page_says_whose_link_it_is_and_signs_nobody_in_until_the_button_is_pressed`, `test_nothing_but_a_press_sends_the_token_to_sign_in` | `Confirm.test.tsx` |
| A link that was asked for elsewhere is asked about a second time, with the address shown again | `test_the_page_says_so_plainly_from_the_start`, `test_a_press_sends_nothing_and_the_page_shows_the_address_again_and_asks_a_second_time`, `test_only_once_the_second_asking_is_answered_is_the_token_sent_with_that_the_person_was_asked`, `test_a_person_who_says_no_is_not_signed_in_and_the_link_is_let_go_unused` | `Confirm.test.tsx` |
| No account is made until the person has said that they are 18 or over | `test_the_page_says_that_an_account_would_be_made_and_asks_the_person_to_say_they_are_18_or_over`, `test_no_account_is_made_until_the_person_has_said_so`, `test_a_tick_is_sent_for_nobody_who_was_not_asked` | `Confirm.test.tsx` |
| The address a person types goes in the body of one request, and what is said after is the same whether or not it has an account | `test_the_address_is_in_the_field_and_in_the_body_of_one_request_and_nowhere_else`, `test_what_becomes_of_asking_is_the_same_whether_or_not_the_address_has_an_account`, `test_what_it_says_does_not_tell_whether_the_address_has_an_account` | `SignIn.test.tsx`, `Sent.test.tsx` |
| What is kept is the spec the page holds, and no word that was typed | `test_a_press_keeps_the_spec_the_page_holds_in_the_body_of_one_request`, `test_what_is_kept_is_what_burro_understood_and_no_word_that_was_typed` | `KeepSearch.test.tsx` |
| A search is sent to be kept among the last ones only where the person lets Burro, and never one that came from a shared link | `test_a_search_that_has_stood_a_while_is_sent_to_be_kept_among_them_where_the_person_lets_burro`, `test_nothing_of_a_search_is_sent_where_the_person_does_not_let_burro_keep_them`, `test_nothing_is_sent_until_the_service_has_said_whether_they_do`, `test_a_search_that_came_from_a_link_somebody_shared_is_not_the_persons_own_and_is_not_sent`, `test_whether_they_are_kept_is_asked_again_of_the_next_person_who_does_not_let_burro_keep_them`, `test_whether_they_are_kept_is_asked_again_of_the_next_person_who_lets_burro_keep_them`, `test_whether_the_last_searches_are_kept_is_let_go_of_as_the_person_who_is_signed_in_changes` | `KeepSearch.test.tsx`, `src/lib/account/who.test.ts` |
| A search is sent to be kept among the last ones only for the person who was signed in as it was made | `test_a_search_that_stands_as_another_person_signs_in_is_not_sent_to_be_kept_for_them`, `test_a_search_that_was_made_while_nobody_was_signed_in_is_not_sent_to_be_kept_for_whoever_signs_in_next`, `test_whose_a_search_is_is_held_while_the_search_page_is_left_and_come_back_to`, `test_the_search_that_stands_is_not_theirs_who_signs_in_after_it_was_made`, `test_the_search_that_stands_is_nobodys_to_have_kept_once_the_person_who_made_it_%s`, `test_a_search_that_was_made_while_nobody_was_signed_in_is_not_theirs_who_signs_in_next` | `KeepSearch.test.tsx`, `src/lib/account/who.test.ts` |
| What one person saved is not said to be saved to whoever signs in after them | `test_what_one_person_saved_is_not_said_to_be_saved_to_whoever_signs_in_after_them`, `test_an_answer_that_comes_once_somebody_else_has_signed_in_is_not_said_to_them` | `KeepSearch.test.tsx` |
| Nothing of an account is put in an address or in anything the browser keeps | `test_nothing_of_the_account_is_put_in_an_address_or_in_anything_the_browser_keeps`, `test_the_id_of_a_session_is_drawn_nowhere_and_put_in_no_attribute`, `test_nothing_in_the_source_touches_storage_the_console_or_the_address` | `Account.test.tsx`, `test/privacy/source.test.ts` |
| The copy is offered as a file that leads to no server, and the page draws none of it | `test_it_is_asked_for_at_a_press_and_offered_as_a_file_that_leads_to_no_server`, `test_the_file_holds_what_the_service_gave_and_the_page_draws_none_of_it` | `Account.test.tsx` |
| Deleting asks a second time, and a person who signed in long ago is told to sign in again | `test_a_press_asks_a_second_time_and_sends_nothing`, `test_a_person_who_signed_in_long_ago_is_told_to_sign_in_again_and_is_offered_no_button_that_deletes` | `Account.test.tsx` |
| The pages of accounts are built the same for everybody, send no referrer, and are never indexed | `test_the_page_is_built_the_same_for_everybody_and_holds_nothing_of_anybody`, `test_it_sends_no_referrer`, `test_every_one_of_them_asks_to_be_left_out_in_its_own_markup_whatever_the_rule_of_the_website_says` | `test/account/pages.test.tsx` |
| A page that the browser puts away holds nothing of an account, and asks again when it is shown. Somebody who is signed in is asked about again as they come back to the tab | `test_nothing_of_the_account_is_drawn_or_held_once_the_page_is_put_away`, `test_a_person_who_signed_out_meanwhile_is_not_shown_to_whoever_presses_back`, `test_the_page_a_link_opens_lets_go_of_the_link_and_of_whose_it_is`, `test_the_page_that_says_a_link_was_sent_lets_go_of_the_address_that_was_typed`, `test_the_page_of_signing_in_does_not_say_who_was_signed_in_before_it_has_asked_again`, `test_somebody_who_is_signed_in_is_asked_about_again_as_they_come_back_to_the_tab` | `test/account/away.test.tsx`, `AccountEntry.test.tsx` |
| A person who signs out, or deletes their account, leaves no search in the tab, and a sign-out that failed leaves it as it was | `test_signing_out_of_this_browser_leaves_no_search_in_the_tab`, `test_signing_out_everywhere_leaves_no_search_in_the_tab`, `test_deleting_the_account_leaves_no_search_in_the_tab`, `test_a_sign_out_that_failed_leaves_the_search_of_the_tab_as_it_was` | `Account.test.tsx` |
| A page that was opened for one person begins again once the service says that another is signed in | `test_a_page_opened_for_one_person_begins_again_once_the_service_says_that_another_is_signed_in` | `Account.test.tsx` |
| The entry of the name board stands after the three pages, as an item of their list, and is drawn as they are | `test_the_entry_stands_after_the_three_pages_as_an_item_of_their_list_and_is_drawn_as_they_are` | `AccountEntry.test.tsx` |
| The stand-in that the website's tests run against refuses as the contract does | `test_what_it_refuses_with_is_a_refusal_of_the_contract`, `test_a_link_that_was_asked_for_elsewhere_is_not_taken_without_being_asked_and_no_account_is_made_unsaid` | `test/account/standin.test.ts` |

**What no test holds**, and a person must:

| What | Why no test |
|---|---|
| That a mail arrives, and that the link in it is the link the service wrote | No test reaches a company that sends mail. Each sender has met a stand-in only |
| That the website and the service work together | Each was built against the contract, and tested against a stand-in for the other. No answer of the service was recorded for the website's tests when accounts were built. Run together, the two were walked in a real browser on 2026-09-26, at the size of a phone and of a desk, on one machine: a link was asked for, opened and pressed, a search was kept and opened again, a visit among them, and the person signed out |
| That the token of a link is in nothing a script can read | No page can change the browser's own record of how it was loaded (section 4, step 9) |
| That the page of an account writes nothing to the console of a person who is not signed in | It asks route 20, which is answered 401 to them, and a browser writes every such answer to its console. The page draws what it should. Route 18 is answered 200 either way, for the name board, so that it writes none |
| That the header the website's host gives holds the address of the client | It is the host's to say. [The guide to deployment](../../deploy/README.md#turning-accounts-on), step 11, tries it |
| That the website passes back no more than 4 MiB | The rule is in `pass.ts`. No test was written for it |
| That the volume is ciphered, and how long its daily copies are kept | They are settings of the host |
| The words a person reads, for their manner | A person reads them, by [the guide to the words](words.md) |

## 13. What is the founder's, and is not decided here

| # | What | Where the choice is set out |
|---|---|---|
| 1 | Who sends the email. A company that sends mail is given every address, and most charge past an allowance | [The guide to deployment](../../deploy/README.md#turning-accounts-on) |
| 2 | The domain, which accounts cannot be turned on without | The same |
| 3 | A volume for the file, and how long the host keeps its daily copies of it | The same, and [ADR 0045](../adr/0045-the-service-has-a-database-one-file-for-accounts-and-what-they-keep.md) |
| 4 | How long what is kept is kept, and what the privacy notice says of it | [The legal drafts](../legal/README.md), under "What accounts changed" |
| 5 | Whether a person's last searches are kept from the start | Section 7, and [ADR 0044](../adr/0044-a-person-who-has-signed-in-may-keep-a-search-and-what-is-kept-is-the-spec-and-never-the-words.md) |

## 14. What is left out, and how it attaches later

| Left out | How it attaches |
|---|---|
| The iPhone app | It has no accounts. A link in a mail opens a browser, and the app holds no cookie of the website's. The contract lists the routes, so its models are generated as any are. What it needs first is a way for a link to open the app, or a code typed by hand beside the link ([ADR 0043](../adr/0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md)) |
| A second way to sign in: a passkey, or a code | Beside the link, which stays as the way back in. Each needs a decision first |
| Changing the address of an account | No route does. A person makes a new account and deletes the old. It would be a link to the new address and a notice to the old, and the second is a mail that is no link to sign in |
| A mail that is no link to sign in | `Sender` has one method, which sends a link. A notice that an account is about to be deleted, or that accounts are withdrawn, is a second method, and a sentence of the privacy notice first |
| Deleting an account that nobody signs in to | Nothing deletes one by its age. The file holds when each session was last put forward, so what is not used can be told. How long is the founder's to set, and whether a person is written to first |
| Signing everybody out at once | No command does it. It is one statement, and is asked for where a secret or the file may have been read ([the guide to deployment](../../deploy/README.md#turning-accounts-on)) |
| A shortlist of areas | A table of an account and the id of an area, and routes under `/v1/me`. It holds nothing of a search |
| A name that a person gives a search | Never as typed text ([ADR 0044](../adr/0044-a-person-who-has-signed-in-may-keep-a-search-and-what-is-kept-is-the-spec-and-never-the-words.md)) |
| The shares, and the records of calls, in the file | Each is a table more, and a decision of its own ([ADR 0045](../adr/0045-the-service-has-a-database-one-file-for-accounts-and-what-they-keep.md)) |
| A cap for each account on calls to a model | `admit` in `app.py` is the place. None is built: a search asks for no account ([ADR 0032](../adr/0032-calls-to-a-model-are-capped-for-the-whole-service.md)) |
| A check for a bot | None. What stands in front of the routes of accounts is the limits, and the firewall of the website's host |
| A third company that sends mail | A row of `COMPANIES` in `accounts/sender.py`, a name in `SenderName`, and the tests beside them |
| A copy of the file kept elsewhere than the host's daily copies | A step that ciphers it and sends it to a bucket, and a line of the privacy notice ([ADR 0045](../adr/0045-the-service-has-a-database-one-file-for-accounts-and-what-they-keep.md)) |
| Answers of the service, recorded for the website's tests | `make web-record` records none of accounts. The website's tests of accounts run against a stand-in, which a test holds to the contract |
