# Accounts: what is left to do

For the founder. Written 2026-09-27, to be picked up later. Tick things off here.

This is the short way through [the guide to deployment, "Turning accounts on"](../deploy/README.md#turning-accounts-on), with the names that were chosen filled in. Where the two differ, the guide is right and this page is out of date. **Nothing here was run on a host.**

## Where things stand

| | |
|---|---|
| The company that sends | Postmark. An account was opened on 2026-09-27, and nothing is set up in it yet |
| A domain | `muscaglar.com` is the founder's. The plan below puts Burro under it |
| The code | Built, tested and off. [The design of accounts](design/accounts.md) says what is built |
| The website that is served | At `burro-silk.vercel.app`, from code that knows nothing of accounts |
| Decided | Who sends. Nothing else below is decided |

Nothing here holds up a deploy. Accounts are off until two settings say `on`.

## The names

| | Name |
|---|---|
| The website | `burro.muscaglar.com` |
| The service | `api.burro.muscaglar.com` |
| Where an email to sign in comes from | `sign-in@burro.muscaglar.com` |

Why a name under the domain, and not the domain itself:

- Whatever mail the domain already has is not touched. Every record below is made under `burro.`.
- If an email to sign in is ever taken for spam, the harm stays with that name.
- The two cookies of accounts are held to the one host, so nothing else under the domain can read them.

To use another name, change it everywhere on this page before you begin. The three must agree, to the letter.

## What it costs

| | |
|---|---|
| Your time | About a day and two more for the notice. [The launch checklist](legal/data-protection-checklist.md#before-accounts-are-turned-on) puts its twelve steps at about 15 hours |
| Money | The paid plan of the website's host, the company that sends past its allowance, a small disk at the service's host, and the regulator's fee for the year. No price is given here: read each on the day |

## 0. First, deploy what is built

Accounts reach the website only after all of this.

| | Task | Where it is said how |
|---|---|---|
| ☐ | See whether the website's host deploys at every push to `main`. If it does, a push puts the new website before the old service | [The website on Vercel](../deploy/web/README.md#when-the-website-is-deployed-again) |
| ☐ | Bring the build into `main` | |
| ☐ | Build London again, and commit its lock | [Data builds](data-builds.md#before-the-service-is-deployed-again) |
| ☐ | Deploy the service, and then the website | [The guide to deployment](../deploy/README.md#serving-a-release-of-london) |

## 1. Decide

Seven things are yours, and the privacy notice has a blank for each. [The legal drafts](legal/README.md#what-is-the-founders-to-decide-and-what-each-choice-costs) say what each choice costs.

| | | What | As it is built |
|---|---|---|---|
| ☐ | A | How long an account is kept when nobody signs in to it | For as long as Burro runs. A limit needs a step that deletes, which is not built |
| ☐ | B | How long a search that was kept is kept | Until the person takes it away |
| ☐ | C | How long the records of links, and of sign-ins that have ended, are kept | A link for a day, a sign-in that has ended for 30 days, what has happened to an account for 90 days |
| ☐ | D | How many days the host keeps its daily copy of the disk | 5, unless it is set. From 1 to 60. The notice must say this number |
| ☐ | E | Whether a person's last searches are kept from the moment they sign in | Only once they turn it on. `BURRO_ACCOUNTS_KEEP_RECENT` chooses |
| ☑ | F | Who sends the email | Postmark |
| ☐ | G | Whether the cookie that keeps a person signed in is set without asking | Set for 30 days. A box to tick, "keep me signed in", is not built |

If nothing is to change, decide D, and write the others down as they are built.

## 2. See what the domain holds today

```
dig +short NS muscaglar.com             # where its names are kept
dig +short MX muscaglar.com             # whether it already takes mail
dig +short TXT _dmarc.muscaglar.com     # whether it says who may send for it
```

| | Task |
|---|---|
| ☐ | Note where the names are kept. Every record below is made there |
| ☐ | If it is Cloudflare: every record below is **DNS only**, the grey cloud |

**Why the grey cloud.** With the proxy on, Cloudflare reads every request, which holds what a person typed: [the guide](../deploy/README.md#a-domain-once-there-is-one) says so. It also stands before the website's host, which then sees Cloudflare's address in the place of each visitor's. The limits on signing in count by that address, so a few people could use up what everybody is allowed.

## 3. Set up the company that sends

[The guide](../deploy/README.md#the-company-that-sends-email) has what to ask of a company, and what Postmark says of itself.

| | Task |
|---|---|
| ☐ | Make a server for Burro alone |
| ☐ | Use the stream for transactional mail, and not the one for broadcasts |
| ☐ | In the settings of the server, leave the counting of who opened a mail and the following of links off |
| ☐ | Add the domain `burro.muscaglar.com` as a sender |
| ☐ | Make the two records the company shows, one for DKIM and one for the return path, where the names are kept. Have the company verify them |
| ☐ | Ask for approval. A new account is on trial, and sends only to addresses of the sender's own domain. Say that Burro sends links to sign in and nothing else |
| ☐ | Put the token of the server in your password manager. Never in a chat, a file or a command line |
| ☐ | Save a dated copy of the company's agreement on data processing |

To check in the company's own pages, because nobody has:

- Whether a token can be held to sending alone. If it cannot, whoever holds it may read whom the server wrote to. That is why Burro has a server of its own.
- How long an email is kept. The page that was read says 45 days unless it is changed. The privacy notice must say the number.
- That following and counting are off for the server. The service also turns both off in every email it sends.

## 4. The paid plan of the website's host

| | Task |
|---|---|
| ☐ | Move the project to the paid plan |

With accounts on, an address of email passes through the website's host. Its agreement on data processing is for its paid plans, as it was read, and its free plan is for work that is not commercial.

## 5. The regulator

| | Task | Where |
|---|---|---|
| ☐ | Decide who runs Burro: a person, or a company | [The launch checklist](legal/data-protection-checklist.md#1-decide-who-runs-burro), task 1 |
| ☐ | Pay the data protection fee, in that name | [Task 2](legal/data-protection-checklist.md#2-pay-the-data-protection-fee) |

## 6. The privacy notice and the terms

This is the long one.

| | Task |
|---|---|
| ☐ | Fill the blanks marked `[FOUNDER]` in [the privacy notice, section 20](legal/privacy-notice.md#20-if-you-make-an-account), with what step 1 decided |
| ☐ | Name the company that sends, where it keeps an email, and for how long |
| ☐ | Work through ["Before accounts are turned on"](legal/data-protection-checklist.md#before-accounts-are-turned-on): twelve steps |
| ☐ | Have the notice and the terms published as pages of the website, with a link to the notice where a person asks for a link to sign in |

No page of the website shows the notice yet. The last row is work on the website, which waits on the words.

## 7. Move the website and the service to their names

[The guide, "A domain, once there is one"](../deploy/README.md#a-domain-once-there-is-one). Nobody has tried it. Replace `APP` with the name of the app at Fly.io.

| | Task |
|---|---|
| ☐ | `fly certs add api.burro.muscaglar.com --app APP`, and make the record it prints: a `CNAME` from `api.burro` to `APP.fly.dev` |
| ☐ | `fly certs check api.burro.muscaglar.com --app APP`. If no certificate has come in a few minutes, `fly certs show` names a record to add |
| ☐ | At the website's host, add `burro.muscaglar.com` to the project's domains, and make the record it shows |
| ☐ | In `deploy/api/fly.toml`, set `BURRO_ALLOWED_ORIGINS` to both origins for as long as the move takes, with a comma between: `"https://burro-silk.vercel.app,https://burro.muscaglar.com"` |
| ☐ | At the website's host, for Production: `BURRO_SITE_URL` is `https://burro.muscaglar.com`, and `NEXT_PUBLIC_BURRO_API_URL` is `https://api.burro.muscaglar.com` |
| ☐ | Deploy the service, and then the website. Make [the checks of step 4](../deploy/README.md#4-confirm-it-worked) again, at the new names |
| ☐ | Once the old address is used no longer, take it out of `BURRO_ALLOWED_ORIGINS` |

Move the website before accounts are turned on, and not after. A session is a cookie of the website's host, so a move signs everybody out. And an email from one name with a link to another reads as a forged one, to a person and to a filter.

## 8. The disk

Decide D of step 1 first. It is the `5` below.

```
fly volumes create burro_accounts --app APP --region lhr --size 1 --snapshot-retention 5
fly volumes list --app APP
```

| | Task |
|---|---|
| ☐ | Make the volume. Never give `--no-encryption` |
| ☐ | In `deploy/api/fly.toml`, take the marks off `[mounts]`, and off nothing else |
| ☐ | Commit and deploy, so that the machine starts with the disk and with accounts still off |
| ☐ | Give the folder to the user the service runs as: `fly ssh console --app APP -C "chown 10001:10001 /data"` |
| ☐ | See that it is so: `fly ssh console --app APP -C "ls -ld /data"` |

## 9. The settings

**At the service, in `deploy/api/fly.toml` under `[env]`.** They stand ready, marked out. None is a secret.

```
BURRO_ACCOUNTS = "on"
BURRO_ACCOUNTS_DB = "/data/accounts.db"
BURRO_ACCOUNTS_SITE = "https://burro.muscaglar.com"
BURRO_ACCOUNTS_SENDER = "postmark"
BURRO_ACCOUNTS_SENDER_FROM = "sign-in@burro.muscaglar.com"
```

Commit. Do not deploy yet.

**The secrets.** Make two, and keep both in your password manager:

```
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Then `fly secrets import --app APP`, type three lines, and end the input. They are read from the keyboard, so none is kept in the shell's history.

| Name | What it holds |
|---|---|
| `BURRO_WEBSITE_SECRET` | The first |
| `BURRO_ACCOUNTS_LIMITS_KEY` | The second. The service does not start where the two are the same |
| `BURRO_ACCOUNTS_SENDER_KEY` | The token of step 3 |

**At the website's host, for Production alone.**

| Name | What it holds |
|---|---|
| `BURRO_WEBSITE_SECRET` | The first again. Mark it as sensitive |
| `BURRO_CLIENT_ADDRESS_HEADER` | `x-vercel-forwarded-for` |
| `NEXT_PUBLIC_BURRO_ACCOUNTS` | `on` |

| | Task |
|---|---|
| ☐ | The five settings in `fly.toml`, committed |
| ☐ | The three secrets, at the service's host |
| ☐ | The three settings, at the website's host |

[The guide, "The settings, in short"](../deploy/README.md#the-settings-in-short) has every setting.

## 10. Deploy, the service first

A website that offers a sign-in which the service does not serve tells a person that Burro has nothing at the address.

| | Task |
|---|---|
| ☐ | Deploy the service |
| ☐ | See that it started with accounts on, and that it answers nobody but the website, as below |
| ☐ | Deploy the website |

```
fly logs --app APP --no-tail | grep -E '"event":"(starting|accounts_on)"' | tail -2
# "event":"accounts_on", after "event":"starting"

curl -sS -o /dev/null -w '%{http_code}\n' https://api.burro.muscaglar.com/v1/auth/session
# 403. A 404 says that accounts are off at the service

fly ssh console --app APP -C "ls -l /data"
# accounts.db and two files beside it, each -rw-------
```

Where the service does not start, `fly logs --app APP --no-tail` names the setting at fault, and never what it was set to. Step 7 of the guide has what each name means.

## 11. Walk it, and read what was written down

| | Task |
|---|---|
| ☐ | Ask for a link, with an address of your own. Read the email as it arrived |
| ☐ | The link leads to `https://burro.muscaglar.com/sign-in/confirm` and nowhere else, with nothing of the company's in its place |
| ☐ | The page says whom it would sign in, and signs nobody in until the button is pressed |
| ☐ | Open a second link in another browser: the page says so, and asks twice |
| ☐ | Keep a search, and open it again from the page of the account |
| ☐ | Take the copy. Sign out. Delete the account |
| ☐ | In the browser's own tools: two cookies and no more, `__Host-burro_link` and `__Host-burro_session`, and nothing in its storage |
| ☐ | The address you used is nowhere in the log: `fly logs --app APP --no-tail \| grep -ci 'THE-ADDRESS-YOU-USED'` prints `0` |
| ☐ | The limits count people. Step 11 of the guide has the loop: 202 ten times, and then 429 |
| ☐ | From a second machine, on another connection, one ask gets 202 |

## When something goes wrong

| To | Do this |
|---|---|
| Turn accounts off for a while | Set `BURRO_ACCOUNTS = "off"` in `fly.toml` and deploy. Take `NEXT_PUBLIC_BURRO_ACCOUNTS` away at the website's host and deploy. The file is kept, and is not opened |
| Replace a secret that may have been read | [The guide, "When a secret is lost"](../deploy/README.md#when-a-secret-is-lost). For the token of the company that sends: revoke it there first, and ask what was read with it |
| Put the file back as it was | [The guide, "The file"](../deploy/README.md#the-file-keeping-it-putting-it-back-and-ending-it). Every account that was deleted since that copy comes back: read it first |
| Sign everybody out | Not built |

## Try it on a machine of your own first

It needs no domain, no company that sends and no disk: the link is written to the terminal, and no email is sent. [The guide, "On a machine of your own"](../deploy/README.md#on-a-machine-of-your-own) has the commands for the service and for the website, and what was seen when it was tried.

## What is not built, and waits on a choice

| | It waits on |
|---|---|
| The change to `deploy/api/fly.toml`: both origins, and the five settings | The name, and the day of the move |
| The pages of the notice and of the terms, and the link to the notice where a person asks for a link | The words of step 6 |
| A step that deletes an account nobody has used | A of step 1 |
| A box to tick, "keep me signed in" | G of step 1 |
| A way to sign everybody out | Nothing. It is asked for where a secret or the file may have been read |
| A third company that sends | A row of `COMPANIES` in `services/api/src/burro_api/accounts/sender.py`, and the tests beside it |

## What nobody has checked

- Nothing was sent through the company. There was no key to send with.
- The steps for a domain, for the disk and for turning accounts on were read, and never run on a host.
- What each company says of itself was read on 2026-09-26, through a reader that summarises. A quoted sentence may differ from its source by a word.
- Whether the service's host gives the folder of the disk to the user of the image by itself.
- Whether the website's host writes over `x-vercel-forwarded-for`, whatever a visitor sent. Step 11 tries it.
- Accounts were reviewed as code and driven on a developer's own machine, and never on a host. [What could go wrong](design/accounts-threats.md) says what each part guards against. Have somebody who did not build them try them on the host before people sign in.
