# 0045. The service has a database, one file, for accounts and what they keep

Status: accepted, 2026-09-26, as groundwork. It follows from [0043](0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md) and [0044](0044-a-person-who-has-signed-in-may-keep-a-search-and-what-is-kept-is-the-spec-and-never-the-words.md): an account that a deploy forgets is no account. It departs from [the plan](../PLAN.md), section 5, which had Postgres at another company. No file has been opened on a host, and what is said of the host below was read on its pages and not tried. The volume, and how long its snapshots are kept, are the founder's to decide.

## Context

- The service had no database. It held one release in memory, with the shares and the records of calls, and wrote nothing to disk ([the contract](../design/contract.md), section 10.1). A deploy forgot every share.
- The machine that ran reached no bucket, held no key but a model's and needed no network to start: the release is inside the image ([0030](0030-a-release-is-kept-approved-by-its-lock-and-carried-in-the-image.md)).
- A token that signs a person in must work once. To check that it was not used and to mark it used are one step or they are a fault, so what holds accounts must have transactions.
- The service runs on one machine, and must: a share is in its memory.
- A new dependency needs a reason, the standard library is preferred, and no package may ship a native binary that it needs to run (rule 12, [0008](0008-package-sources.md)).
- There is one founder. Each company that holds what is a person's is one more agreement, one more check of where it is kept, and one more line of the privacy notice.

## Decision

**What accounts keep is kept in SQLite, through the `sqlite3` module of Python's standard library: one file, on a volume of the host that is ciphered at rest and lasts from one deploy to the next.**

| Matter | What is so |
|---|---|
| What is in it | Accounts, the hashes of the tokens of links and of sessions, the searches that are kept and the last ten, preferences, and what happened to an account. [The design](../design/accounts.md), section 3, has each table |
| What is not | Anything of a release, of a place or of a call. The shares and the records of calls stay in memory, as they were. Nothing that was typed |
| How it is opened | With write-ahead logging, foreign keys on, and a wait of five seconds for a lock before a statement gives up. The service reads each setting back, and does not start on a file that is not set so |
| What is deleted | Is written over in the file with noughts, and not only let go of. So an account that is deleted is gone from the file, and not only from its tables |
| What is taken away | Is taken out of the file and of what is written beside it, as an account that is deleted is: a search that a person takes away, the last searches that they have Burro forget or turn off, and the oldest of the last ten as it goes. What was written ahead of the file is brought into it, and cut to nothing. **Amended on 2026-09-26, the day it was built**, after what was built was tried: a search that was taken away was out of the tables, and stayed in what is written ahead of the file, with the place its journey leads to, until an account was deleted or a day's links were let go of |
| Whose the file is | Its owner's alone, to read and to write: the user the service runs as |
| How it is asked | Every statement binds its values. None is ever made by putting strings together |
| Who touches it | One small layer holds the connection. No route and no other module opens the file or writes a statement |
| Its layout | Has a version, which the file holds. Changes to it are applied as the service starts, forward only, under a lock |
| With accounts off | No file is opened, and none is made. The service is what it was |
| Where it stands | On a volume that the host ciphers at rest. The setting that names the file is needed at start where accounts are on |

Why this one:

| Reason | |
|---|---|
| It adds no dependency | `sqlite3` is in the standard library. The check of what the service imports does not change |
| It adds no company | The file is on the host that runs the service already, which sees every request as it is |
| It adds no network and no credentials | A database at another host is reached over a network, with a password that the service would hold and could lose |
| It has transactions | A token is checked and marked in one. An account goes with everything of it in one |
| It is small enough to read | Seven tables, a layer of one module, and no tool that writes statements for it |
| The file is all that Burro holds of anybody | To copy it, to keep it and to delete it are each one act, on one thing |

What was weighed, and put aside:

| Way | Why not |
|---|---|
| Postgres at another company, with its sign-in, as the plan had it | A second company that would hold every address and every kept search. A driver to install, a password to hold, a network to reach before a person can sign in, and a bill by the month |
| Postgres on the host's own machines | A second machine to run and to watch, and the driver, the password and the network all the same |
| Files of lines, as the review desk keeps its decisions | No transaction. Between the check of a token and its mark, a second request would find it unused |
| Memory, as the shares are kept | A deploy would sign everybody out and lose every kept search |
| A tool that maps records to tables, or one that manages changes of layout | Each is a dependency, for seven tables and a handful of changes |
| The shares and the records of calls in the same file | Neither is of an account, and neither was asked for. It is one change to move them, and it is left for its own decision |

## Consequences

- **The machine needs more than its image to start**, where accounts are on: its volume, three secrets, and a network to reach the sender of email. With accounts off it needs what it needed.
- **One machine, and no more.** The host says of a volume, as read: "A volume exists on one server in a single region", and that it attaches to one machine. It was so already, for the shares.
- **If the drive fails, the accounts go back to the last snapshot, or are lost.** The host, as read: "Always provision at least two volumes per app. Running an app with a single Machine and volume leaves you at risk for downtime and data loss." Burro runs one. The host takes a snapshot of a volume each day and keeps it for five days unless it is set otherwise, from one day to sixty.
- **A snapshot holds what was deleted since it was taken.** An account that a person deletes is gone from the file at once, and is in the host's snapshots until the last of them that held it is let go. The privacy notice says so, and how long that is follows from a setting of the volume. **To put a snapshot back is to bring back what was deleted since**, and nothing in the file says what that was: [what could go wrong](../design/accounts-threats.md) has it among what nothing holds.
- **To roll the code back is not to roll the file back.** An image of before a change of layout would meet a layout it does not know. Changes go forward only, so the code that goes back must be code that knows the layout, and [the guide to deployment](../../deploy/README.md#turning-accounts-on) says what to do.
- **One writer at a time.** A write waits for the write before it. At the size of Burro it is a wait of a thousandth of a second, and the ranking, which reads no file, does not wait at all.
- **A volume is charged for**, by its size and by the hour, whether or not the machine runs, and so are its snapshots past an allowance. No price is given here: read the host's own page on the day.
- **Whoever can read the machine can read the file.** That the volume is ciphered at rest keeps a drive that is taken from being read. It does not keep the host, or whoever holds the founder's sign-in at the host, from the file. What is in it is therefore as little as will do: hashes where a hash will do, and no address of a client.
- What holds it: [the design](../design/accounts.md), section 12, names the tests. Among them, that no statement is made of strings, that with accounts off no file is opened, and that a layout of an older version is brought forward once.

## What would change it

| If | Then |
|---|---|
| A second machine | One file on one volume will not do. Postgres, or a file that is copied from one machine to the others as it is written, and a decision for each |
| More writes than one writer takes | It would show as writes that give up after their wait. None is expected at this size |
| The founder wants a copy of the file kept elsewhere than the host's snapshots | A step that copies it to a bucket, ciphered first, with a key that is kept apart. It is one more place that holds what is a person's, and one more line of the privacy notice |
| The shares are to outlive a deploy | A table of the same file. [0011](0011-nothing-is-kept-for-a-search.md) holds what a share may keep |
| The host stops ciphering a volume at rest, or a volume is made without it | Accounts are not turned on there. As the host's page was read, a volume is ciphered unless it is made with the flag that says otherwise |
