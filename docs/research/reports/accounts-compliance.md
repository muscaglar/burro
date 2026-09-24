# accounts-compliance: Accounts, subscriptions and compliance for a UK consumer product on web and iOS (Burro)

## Headline
Buy auth, do not build it: Supabase Auth in the London region with Sign in with Apple + Google + email one-time code, anonymous use for search, and in-app account deletion. Build a small provider-agnostic entitlements table now (everyone on a "free" plan) and add RevenueCat over StoreKit 2 and Stripe only when premium launches; on the UK App Store premium must be sold through Apple In-App Purchase because external purchase links are still not permitted in the UK (CMA steering rule is proposed, not decided, as of 23 Sep 2026). Keep ethnicity, religion, country of birth, language, sexual orientation and disability/health data out of ranking, filters and LLM context entirely; match on amenities, not on who lives there. Treat free-text prompts as possibly special category data: extract structured preferences, do not store raw prompts beyond short-lived logs, get explicit in-app permission before sending text to Anthropic (Apple 5.1.2(i)), write a DPIA, pay the ICO fee (GBP 52), and ship one "Data sources and licences" page plus on-map attribution.

## Summary
Checked against primary sources on 23 Sep 2026 (Apple guidelines, ICO, GOV.UK/CMA, legislation.gov.uk, Ofcom, vendor pricing pages, licence texts). Some items rest on a page opened at a known address, and some are flagged unverified.

MUST-HAVE FOR LAUNCH
Accounts
- Search, map, area profiles, comparison and shared links work with no login (Apple 5.1.1(v)). Login only for saved shortlists.
- Sign in with Apple, Google, and email one-time code. If Google is offered, Apple 4.8 requires an equivalent privacy-preserving login; Sign in with Apple satisfies it.
- In-app account deletion, easy to find, deleting the whole account record; revoke Sign in with Apple tokens via Apple's REST API; same flow on web.
- Demo account and review notes for App Review (2.1).
Entitlements
- `plans`, `entitlements` and a single `require_entitlement()` check in the Python API from day one; every user has plan=free with all features. No payment code in v1.
Data protection
- ICO fee paid before launch (tier 1 GBP 52, GBP 47 by direct debit).
- Privacy notice (Art 13), data protection complaints route with 30-day acknowledgement (DUAA, in force 19 Jun 2026), DSAR/erasure process, retention schedule, record of processing, processor list (Anthropic, hosting, auth, email, analytics).
- DPIA (AI + possible special category data + profiling-like personalisation).
- Prompt handling: structured extraction schema with no protected-characteristic fields; raw prompt not persisted in the product database; operational logs with raw text max 30 days; notice by the prompt box.
- Anthropic: Commercial Terms + DPA (UK addendum), no training on customer content, 30-day default deletion; AI disclosure at start of each chat session (Anthropic usage policy) and notice that outputs may be inaccurate (Commercial Terms).
- iOS: explicit permission screen before first prompt is sent to a third-party AI (5.1.2(i)); App Privacy labels; privacy manifest.
- Web: cookieless or first-party analytics under the PECR statistical-purposes exemption with clear information and an opt-out; no ad tech; marketing email opt-in.
Fairness and harm
- Written data-use policy: protected-characteristic composition is never an input to ranking, filters, vibe tags or LLM context. Requests like "fewer/more people of X" get a fixed refusal with amenity-based alternatives.
- Same query gives same results for every user; no personalisation on inferred user traits.
- Offline proxy audit: check each ranking feature's correlation with Census ethnicity/religion shares; document in DPIA.
- LLM explanations are generated only from retrieved facts with source and date; banned vocabulary list ("rough", "dodgy", "safe", "unsafe", "up-and-coming" without data); crime shown as recorded-crime rates by category with caveats.
- "Report a problem with this area" link and a corrections process.
- WCAG 2.2 AA on web; VoiceOver, Dynamic Type, contrast, reduced motion on iOS; non-map list alternative for every map view.
Attribution
- On-map attribution (OpenStreetMap, OS) plus an in-app and web "Data sources and licences" page carrying every required statement; attribution stored as metadata per dataset in the repo.
App Store
- Native value beyond a web wrapper (MapKit, saved shortlists, share sheet, offline shortlist); updated age-rating questionnaire; built with Xcode 26 / iOS 26 SDK.

LATER
- Premium: StoreKit 2 + RevenueCat + Stripe; DMCC subscription regime compliance (commences January 2027); 14-day cooling-off handling; Small Business Program enrolment (15%).
- External purchase link in the UK app if and when the CMA steering requirement is imposed.
- Passkeys (Supabase support is experimental as of May 2026).
- EU storefront distribution (DSA trader status, EU business terms from 1 Oct 2026), VAT via merchant of record if selling outside the UK.
- Any user-generated content or live web search by the LLM: either would bring the Online Safety Act into play; re-assess before building.
- ICO statutory AI/ADM code (expected 2027) and Crime and Policing Act 2026 chatbot powers: monitor.
- Apple Accessibility Nutrition Labels when they become mandatory.

## Recommendations
- **Auth: build or buy, and which vendor** [medium]: Buy. Supabase Auth, project pinned to West Europe (London) eu-west-2, Pro plan (USD 25/month, 100,000 MAU included). Python API verifies Supabase JWTs; Burro keeps its own `users` table keyed by the auth subject id so the vendor can be swapped.
  - why: Fits the budget, UK data residency, native Swift and JS SDKs, native Sign in with Apple via signInWithIdToken, email OTP, and it is also a Postgres host if the data team chooses it. Free tier pauses projects after 1 week of inactivity so Pro is needed for a public launch. Custom SMTP is mandatory for production (default sender is limited to 30 emails/hour and team addresses).
  - rejected: Native Python auth (FastAPI-Users/Authlib): rejected, security and Apple token-revocation burden for no product gain. Other hosted sign-in services: not chosen. No price of theirs is given here, since no page of theirs is cited.
- **Sign-in methods at launch** [high]: Sign in with Apple, Google, and email one-time code (6 digits). No passwords. Passkeys later.
  - why: Guideline 4.8 (verified today) requires an equivalent privacy-preserving login when a third-party login such as Google is used; Sign in with Apple meets the three listed criteria. Email codes are more reliable than magic links on iOS (no universal-link edge cases) and satisfy WCAG 2.2 3.3.8 Accessible Authentication if paste is allowed. Supabase passkeys are experimental (API may change) so defer.
  - rejected: Email-only login would avoid 4.8 entirely but costs conversion. Password login adds breach and reset burden. Passkeys at launch rejected because vendor support is experimental.
- **Login wall** [high]: No login for search, map, profiles, comparison and viewing shared links. Account required only to save shortlists and sync across devices.
  - why: Apple 5.1.1(v): apps without significant account-based features must work without login. Also reduces personal data held and improves conversion for relocators.
  - rejected: Mandatory sign-up before first search: App Review risk and data-minimisation problem.
- **Account deletion** [high]: Settings > Delete account in the iOS app and on web; hard-delete user row, shortlists, saved searches and auth identity; revoke Sign in with Apple tokens through Apple's REST API; confirm by email; if a subscription exists later, tell the user billing continues through Apple and link to manage subscriptions.
  - why: Apple requires in-app deletion of the whole account when account creation is supported; a link to a website alone is not acceptable unless it goes directly to the deletion page. UK GDPR erasure right points the same way.
  - rejected: Deactivate-only or email-us-to-delete: non-compliant with Apple.
- **Entitlements model shared across web and iOS** [high]: Server-side source of truth in Burro's Postgres: plans, features, plan_features, entitlements(user_id, key, source[app_store|stripe|promo|admin], status, period_end, external_ref). API exposes GET /me/entitlements; every gated route calls one dependency. v1 ships with plan=free granting everything. Clients never decide access locally.
  - why: Lets premium be introduced by changing plan_features rows, not code. Works identically for web and iOS and is independent of any billing vendor.
  - rejected: Client-side StoreKit checks only: cannot serve web. Using RevenueCat as the only source of truth: lock-in and no promo/admin grants.
- **Subscription stack when premium launches** [medium]: StoreKit 2 on iOS and Stripe Checkout on web, both fronted by RevenueCat (free to USD 2,500 monthly tracked revenue, then 1%). RevenueCat webhooks update the entitlements table. Enrol in the App Store Small Business Program (15% commission).
  - why: One integration gives receipt validation, renewals, refunds and cross-platform entitlements; cost is zero until there is revenue. Apple 3.1.3(b) lets web-bought subscriptions unlock the iOS app provided the same items are also sold by IAP in the app.
  - rejected: Direct App Store Server API + Stripe webhooks: viable later to save the 1%, more to build and test now. Stripe Managed Payments as merchant of record (GB supported): consider only if selling outside the UK for VAT; checkout is branded as sold through Onelink and custom domains are not supported. Web-only payments with no IAP: breaches 3.1.1 if premium features unlock in the app.
- **External purchase links in the UK iOS app** [high]: None. No buttons, links or wording in the UK app or its metadata that point to web purchase. Revisit when the CMA publishes its final steering decision.
  - why: Guideline 3.1.1(a): outside entitled storefronts and the US, apps may not include calls to action to other purchase mechanisms. CMA proposed a steering conduct requirement on 30 Jun 2026, consultation closed 28 Jul, responses published 14 Aug; no decision and no timetable as of mid-Sep 2026.
  - rejected: Shipping a link now in anticipation of the CMA rule: rejection or removal risk.
- **Lawful bases** [medium]: Contract for accounts and saved shortlists; legitimate interests (with a written assessment) for processing prompts to return results, security logging and product analytics; consent for marketing email and any non-exempt cookies. Do not rely on processing special category data at all: design so none is intentionally inferred or used.
  - why: ICO guidance: an Article 9 condition is needed when you intend to infer a special category or treat someone differently because of it. Extracting only neutral preferences (for example step_free_access=true, near_place_of_worship=mosque as an amenity) and discarding the rest avoids that intent. Explicit consent is the fallback if the founder wants to store raw prompts.
  - rejected: Blanket consent for everything: weak basis and poor UX. Explicit-consent gate before every prompt: unnecessary if raw text is not retained or used for inference.
- **Prompt storage and retention** [high]: Persist the structured preference object, not the raw prompt. Raw text only in operational logs for up to 30 days, excluded from analytics and never shown on shared links. Saved searches store the structured summary. Any evaluation corpus is opt-in or redacted.
  - why: Users will volunteer health, religion, sexuality and family details. Minimising raw text reduces special category exposure, DSAR scope and breach impact, and aligns with Anthropic's own 30-day deletion.
  - rejected: Keep all prompts indefinitely for product improvement: high risk, needs explicit consent and stronger DPIA.
- **DPIA** [high]: Do one before launch, short form, reviewed at each material change.
  - why: ICO lists innovative technology (AI) as requiring a DPIA when combined with another risk factor; free-text that may reveal special category data and location-related profiling supply that factor.
  - rejected: Skip because there is no large-scale special category processing: defensible but leaves no evidence of the fairness and minimisation decisions.
- **LLM processor configuration** [high]: Anthropic API under Commercial Terms and DPA, default 30-day retention, no Files API or other long-retention features for user text, no user identifiers in prompts. Show 'AI-generated from Burro data, may contain errors' next to explanations and an AI disclosure at the start of each chat session.
  - why: Commercial Terms: Anthropic may not train on customer content and customer must notify users not to rely on factual assertions unchecked. Usage policy: consumer-facing chatbots must disclose AI at the start of each session. Flagged content can be kept up to 2 years and classifier scores up to 7 years, which must appear in the privacy notice.
  - rejected: Zero data retention agreement: not needed at launch and requires a sales arrangement. Routing through a cloud reseller changes who the processor is; decide with the infrastructure plan.
- **Cookies and analytics** [medium]: No advertising or cross-site trackers. Cookieless analytics (for example Plausible, from USD 9/month, EU hosted) or first-party analytics, with a plain-language notice and an opt-out. Strictly necessary cookies only for session and auth. No consent banner needed on that basis.
  - why: Since 5 Feb 2026 PECR exempts storage/access for statistical purposes if users get clear information, a simple objection route, and no third party uses the data for its own purposes; ICO guidance finalised 29 Apr 2026. PECR fines now reach GBP 17.5m or 4% of turnover, so keep it simple.
  - rejected: Google Analytics with ad features: needs consent banner and US transfer analysis. No analytics at all: unnecessary.
- **Online Safety Act posture** [medium]: Stay out of scope by design: no user-to-user content, shared links render only system-generated results from structured parameters (no user free text, no user-chosen titles visible to others), and the LLM queries only Burro's own database with no live web search. Record this in an architecture decision record and re-assess before adding notes, comments, reviews or web search.
  - why: OSA s.3 covers services where user-generated content may be encountered by other users; s.229 excludes a service that searches just one website or database. Ofcom (18 Dec 2025) says chatbots that only let people interact with the chatbot itself and do not search multiple websites or databases are out of scope.
  - rejected: Showing the original prompt on shared pages, or public shortlists with user notes: would likely make Burro a user-to-user service with illegal-content risk assessment duties.
- **Use of demographic data** [high]: Three tiers. Allowed in scoring: age structure, household composition, tenure, student share, density, and amenity mix. Never used in scoring, filters, tags or LLM context and not displayed in v1: ethnicity, religion, country of birth, national identity, main language, sexual orientation, gender identity, disability and health. Used offline only: the excluded Census variables, to audit ranking features for proxy effects.
  - why: Equality Act 2010 s.29 bars service providers from discriminating in providing a service; the EHRC Services Code (in force 5 Aug 2026) treats providing information about properties as a service to the public. ICO says removing protected attributes is not enough because proxies remain, so an audit is needed. Apple 1.1.1 and Anthropic's usage policy both prohibit discriminatory content. US experience shows portals withdrew even crime data over steering concerns.
  - rejected: Displaying ethnicity and religion breakdowns on profile pages as neutral facts (common on UK stats sites): lawful data (OGL) but invites steering use, App Review risk and reputational harm; revisit only with legal advice. Letting the LLM answer 'where do people like me live': rejected.
- **Handling steering-type requests** [high]: A classifier step (rules plus LLM) on input and output. Requests about resident composition get a fixed response explaining Burro does not rank by who lives in an area and offering amenity-based options (places of worship, specialist food shops, community centres, venues, schools by type). Test suite of adversarial prompts in CI.
  - why: A stop list plus a classifier on inputs and outputs. Amenity matching serves the legitimate need without using protected characteristics of residents.
  - rejected: Relying on the base model's judgement alone: not testable or explainable.
- **Crime and other negative indicators** [medium]: Include police.uk recorded crime as rates by category, relative to the London distribution, with source, period and caveats; never a single 'safety score' label and never the words safe/unsafe/dangerous. User can set the weight to zero. Town-centre and station effects explained in the UI.
  - why: Data is OGL and widely used in the UK, but locations are snapped to anonymised points and quality varies by force. Redfin said in December 2021 that it would not show neighbourhood crime data (<https://www.redfin.com/news/neighborhood-crime-data-doesnt-belong-on-real-estate-sites/>). Consistency and objectivity are the defensible line.
  - rejected: Omit crime entirely: removes a factor relocators ask for. Composite safety score: hard to substantiate and easy to misread.
- **Claims and negative descriptions** [medium]: Editorial policy in the repo: every generated sentence must map to a retrieved fact with source and date; comparative neutral wording; no naming of individual businesses, estates or streets negatively; no superlatives ('best', 'safest') in product or marketing without documentary evidence; corrections contact on every profile.
  - why: CAP Code rule 3.7 requires documentary evidence for objective claims and applies to marketing on a company's own website and social channels. DMCC Act unfair commercial practices regime (in force 6 Apr 2025) lets the CMA fine up to 10% of global turnover for misleading practices.
  - rejected: Free-form LLM area descriptions: hallucination and complaint risk.
- **Accessibility standard** [high]: WCAG 2.2 level AA for web, Apple accessibility features for iOS, and a list/table equivalent for every map interaction. Publish an accessibility statement.
  - why: No statute mandates WCAG for UK private companies, but the Equality Act duty to make reasonable adjustments applies to all service providers, and WCAG 2.2 AA is the UK public sector benchmark. New 2.2 criteria that matter here: target size (2.5.8), dragging movements (2.5.7, map sliders), accessible authentication (3.3.8), focus not obscured (2.4.11).
  - rejected: WCAG 2.1 AA: superseded. AAA: disproportionate.
- **Attribution implementation** [high]: A `datasets` registry in the repo (name, licence, attribution text, year, URL) that generates the 'Data sources and licences' page for web and iOS; persistent map-corner attribution for OpenStreetMap and OS; keep OSM-derived tables separate from other data and be ready to publish OSM-derived tables under ODbL.
  - why: OGL rights end automatically if attribution is missing. OGL allows a link to a page when multiple statements are impractical. ODbL share-alike applies to derivative databases but not to produced works such as maps.
  - rejected: Attribution only in a footer of the website: misses the iOS app and map views.
- **Age policy** [medium]: Accounts for 18+; document a short assessment that the service is not likely to be accessed by children; answer Apple's updated age-rating questions honestly including the AI assistant question.
  - why: ICO Children's code applies only if access by under-18s is more probable than not; a home-search tool is unlikely to meet that test but the reasoning should be written down.
  - rejected: Age verification: disproportionate.
- **Subscription consumer-law compliance (when premium launches)** [medium]: Design the paywall and lifecycle emails to the DMCC subscription regime from the start: key pre-contract information more prominent than anything else, express acknowledgement of payment obligation, reminder notices, 14-day cooling-off and renewal cooling-off, cancellation in-app and on web in the same medium as sign-up, end-of-contract notice.
  - why: Regime commencement was brought forward to January 2027 (announced 9-10 Aug 2026), which is before or around any realistic premium launch.
  - rejected: Waiting for final guidance before designing: risks a rework of paywall and email flows.

## Risks
- [high] Steering and discrimination: ranking, filters or LLM explanations use or proxy for protected characteristics of residents, or respond differently to users based on perceived characteristics. -> Exclude protected-characteristic variables from scoring, filters, tags and LLM context; input and output classifier with fixed refusal and amenity alternatives; identical results for identical structured preferences; offline proxy audit documented in the DPIA; adversarial prompt tests in CI.
- [high] Users volunteer special category data in free-text prompts (health, religion, sexuality), creating Article 9 exposure, larger DSAR and breach impact. -> Extract neutral structured preferences only; do not persist raw prompts in the product database; 30-day cap on raw text in logs; notice beside the prompt box; explicit consent if raw prompts are ever retained for evaluation.
- [high] LLM states something false or disparaging about an area, business or group, leading to complaints, press attention or ASA/CMA action. -> Explanations generated only from retrieved facts with citations and dates; banned vocabulary and no superlatives without evidence; automated groundedness check before display; visible 'AI-generated, may contain errors' notice; corrections link and takedown process.
- [medium] App Store rejection: missing explicit permission for third-party AI (5.1.2(i)), missing in-app deletion (5.1.1(v)), login options (4.8), forced login, thin wrapper (4.2), no demo account (2.1). -> Pre-submission checklist in the repo covering each guideline; native features (MapKit, offline shortlist, share sheet); review notes explaining data sources and AI use; demo account.
- [medium] UK App Store rules change mid-build (CMA steering decision pending) and Apple's commission or link-out terms differ from assumptions. -> Entitlements abstraction independent of billing provider; price premium assuming 15% Apple commission; watch the CMA case page; add link-out only after Apple publishes UK terms.
- [medium] DMCC subscription regime (January 2027) applies by the time premium launches and paywall or emails are non-compliant. -> Design paywall, reminders, cooling-off and cancellation to the regime from the start; get legal review of how duties apply to Apple-billed subscriptions.
- [medium] Online Safety Act scope creep through shareable links showing user text, public shortlists with notes, or adding live web search to the LLM. -> Shared links carry only structured parameters and system-generated content; no user free text visible to others; LLM limited to Burro's own database; architecture decision record and re-assessment before any UGC or web search.
- [medium] Attribution failure ends OGL rights automatically, or ODbL share-alike is triggered on a mixed database. -> Dataset registry with licence and attribution text generating the credits page; CI check that every dataset in use has a registry entry; keep OSM-derived tables separate and publishable.
- [medium] Crime data misread as a judgement on residents or as precise to street level. -> Rates by category with denominators explained, relative to London, period shown, snap-point caveat, no safety labels, weight adjustable to zero.
- [medium] PECR or UK GDPR breach through analytics SDKs, marketing email without opt-in, or undeclared processors. -> Cookieless analytics only; no ad SDKs; marketing opt-in with unsubscribe; processor register reviewed at each new dependency.
- [low] International transfer of prompts to the US (Anthropic) not reflected in notices or transfer assessment. -> Rely on Anthropic DPA with the UK addendum; complete a short transfer risk assessment; disclose in privacy notice and the iOS permission screen.
- [low] Vendor lock-in for auth or subscriptions. -> Own users and entitlements tables; vendors referenced by external ids only; webhooks as the integration boundary.
- [medium] Inaccessible map-first interface excludes disabled users and invites Equality Act reasonable-adjustment complaints. -> List and table equivalents for all map content, keyboard operation, target sizes, contrast, screen-reader labels, accessibility statement and contact route; test with VoiceOver.


## Open questions
- What legal entity will operate Burro (needed for ICO registration, App Store organisation account, trader details on site and privacy notice)?
- Will the iOS app be available only on the UK storefront at launch, or worldwide including the EU (which triggers DSA trader status and, for paid features, EU business terms)? Relocators abroad argue for worldwide.
- Does the founder accept excluding ethnicity, religion, country of birth and language data from the product entirely in v1, including display on profile pages?
- Does the founder want to retain raw prompts for product improvement or evaluation? If yes, explicit opt-in consent and a redaction step are needed.
- Will shared links or shortlists ever show user-written text (titles, notes)? If yes, Online Safety Act scope needs legal review first.
- Which features are intended to become premium, and is web/iOS price parity required? This affects whether the 15% Apple commission is absorbed.
- Where will the primary database be hosted? The Supabase Auth recommendation is strongest if Postgres is also on Supabase; otherwise WorkOS or Clerk should be re-compared.
- How do DMCC subscription duties divide between Apple and the developer for Apple-billed subscriptions? The government response is silent; needs legal advice before premium launch.
- Is there budget for a one-off legal review (privacy notice, terms, fairness policy, DPIA) before public launch?
- Minimum age for accounts: 18+ as recommended, or lower?
- Do per-neighbourhood aggregates computed from OpenStreetMap places count as an ODbL derivative database that must be offered publicly? Needs a decision with the data workstream.

## Unverified
- DMCC subscription regime commencement in January 2027: confirmed only through law-firm sources (TLT, Wiggin tracker) reporting a Prime Minister's Office announcement of 9-10 Aug 2026; the GOV.UK consultation response still says spring 2027 and no primary announcement page was opened.
- Crime and Policing Act 2026 AI chatbot provisions (scope, definitions, commencement): primary text not read.
- ICO statutory AI and automated decision-making code timing: not read.
- EHRC Services Code passage on an estate agent advertising or providing information about properties: not read. The EHRC site was not read, and the passage was not found in the GOV.UK page as read.
- That Burro's shareable links fall outside the Online Safety Act if they show only system-generated content: my reading of ss.3, 55 and 229 and Ofcom's pages, not confirmed by Ofcom or counsel.
- That extracting neutral structured preferences from prompts avoids the need for an Article 9 condition: my application of ICO inference guidance; ICO does not address free-text prompts directly.
- Stripe Managed Payments fee level and Stripe's UK fee for non-EEA international cards: not read.
- StoreKit 2, App Store Server Notifications V2 and appAccountToken details: from prior knowledge, Apple documentation not re-read today.
- Supabase handling of Sign in with Apple token revocation on account deletion: not documented on the page read; assumed Burro must implement it.
- Supabase DPA contents and subprocessor list: not opened.
- Google Sign-In terms, branding and OAuth verification requirements: not checked.
- Clerk pricing as 'monthly retained users' with 50,000 free: taken from one fetch of the pricing page summary; re-check before relying on it.
- WorkOS native iOS SDK support: not checked.
- Email delivery provider pricing (Resend, Postmark, SES): not checked.
- Census 2021 table licence (OGL v3) for ethnicity and religion tables: inferred from ONS's general licence page for geography products; the Census dataset pages were not opened.
- UK VAT treatment of digital subscriptions sold to UK and non-UK consumers: not researched.
- European Accessibility Act applicability to a UK micro-business with EU users: not researched.
- Defamation and malicious falsehood exposure from negative area descriptions: general legal understanding, no source checked.
- WCAG 2.2 original publication date: not read. The W3C page shows the current Recommendation dated 12 Dec 2024.
- Apple's UK-storefront commission being the standard 30% / 15% Small Business Program rate: taken from Apple's global programme page, no UK-specific page found.
- What App Review accepts in practice as 'explicit permission' for third-party AI under 5.1.2(i): guideline text verified, reviewer practice not.
## Findings (compact)
- App Store Review Guideline 4.8 Login Services | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- App Store Review Guideline 5.1.1(v) and Apple account deletion guidance | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- Supabase Auth | use_v1 | commercial=yes | verified=True | lic=Supabase terms of service; DPA available (not read in this pass) | cost=Free: 50,000 MAU, project paused after 1 week inactivity. Pro: USD 25/month, 100
- Supabase passkeys | use_later | commercial=yes | verified=True | lic= | cost=
- Native Python auth implementation | reject | commercial=yes | verified=False | lic= | cost=
- Apple Developer Program | use_v1 | commercial=yes | verified=True | lic= | cost=USD 99 per year. Commission 30% standard, 15% in the Small Business Program (pro
- App Store Guidelines 3.1.1, 3.1.1(a), 3.1.3(b) | use_later | commercial=not_applicable | verified=True | lic= | cost=
- CMA proposed steering conduct requirement (Apple and Google) | reference_only | commercial=not_applicable | verified=True | lic= | cost=
- Apple EU business terms effective 1 Oct 2026 | reference_only | commercial=not_applicable | verified=True | lic= | cost=
- StoreKit 2 | use_later | commercial=yes | verified=False | lic= | cost=
- RevenueCat | use_later | commercial=yes | verified=True | lic= | cost=Free up to USD 2,500 monthly tracked revenue, then 1% of tracked revenue. Web pa
- Stripe (UK pricing) | use_later | commercial=yes | verified=True | lic= | cost=1.5% + 20p standard UK cards; 2.5% + 20p EEA cards; Billing 0.7% of billing volu
- Stripe Managed Payments | use_later | commercial=yes | verified=True | lic= | cost=
- DMCC Act 2024 subscription contracts regime | use_later | commercial=not_applicable | verified=True | lic= | cost=
- Consumer Contracts Regulations 2013, regulation 37 | use_later | commercial=not_applicable | verified=True | lic= | cost=
- DMCC Act 2024 unfair commercial practices regime (CMA207) | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- ICO data protection fee | use_v1 | commercial=not_applicable | verified=True | lic= | cost=Tier 1 (up to 10 staff or turnover up to GBP 632,000): GBP 52. Tier 2: GBP 78. T
- Data (Use and Access) Act 2025 | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- ICO guidance on storage and access technologies | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- ICO DPIA guidance | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- ICO guidance on special category data and inferences | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- ICO privacy information guidance (Articles 13/14) | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- Anthropic Commercial Terms, DPA and retention policy | use_v1 | commercial=yes | verified=True | lic=https://www.anthropic.com/legal/commercial-terms and https://www.anthropic.com/legal/data-processing-addendum | cost=
- Anthropic Usage Policy | use_v1 | commercial=yes_with_conditions | verified=True | lic= | cost=
- ICO Children's code scope | reference_only | commercial=not_applicable | verified=True | lic= | cost=
- Online Safety Act 2023 (ss.3, 55, 229) and Ofcom chatbot guidance | reference_only | commercial=not_applicable | verified=True | lic= | cost=
- Crime and Policing Act 2026 AI chatbot provisions | reference_only | commercial=not_applicable | verified=False | lic= | cost=
- ICO statutory code on AI and automated decision-making | reference_only | commercial=not_applicable | verified=False | lic= | cost=
- Plausible Analytics | use_v1 | commercial=yes | verified=True | lic= | cost=From USD 9/month (10k pageviews)
- Equality Act 2010 s.29 and s.111, and EHRC Services Code of Practice | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- ICO guidance on fairness, bias and discrimination in AI | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- Redfin, on crime data | reference_only | commercial=not_applicable | verified=True | lic= | cost= | read at <https://www.redfin.com/news/neighborhood-crime-data-doesnt-belong-on-real-estate-sites/>
- Census ethnicity, religion, country of birth and language data in ranking or LLM context | reject | commercial=yes | verified=False | lic=ONS Census outputs are published under OGL v3 (ONS licence page confirmed for geography products; Census table licence not separately opened | cost=
- data.police.uk street-level crime | use_v1 | commercial=yes | verified=True | lic=Open Government Licence v3.0 | cost=
- CAP Code section 3 (misleading advertising) | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- WCAG 2.2 | use_v1 | commercial=yes | verified=True | lic= | cost=
- Apple Accessibility Nutrition Labels | use_later | commercial=not_applicable | verified=True | lic= | cost=
- App Store Guideline 5.1.2(i): third-party AI disclosure | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- App Store Guidelines 4.2, 1.1.1, 2.1, 2.3.1, 5.1.1(i) | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- Apple upcoming requirements and age ratings | use_v1 | commercial=not_applicable | verified=True | lic= | cost=
- Open Government Licence v3.0 | use_v1 | commercial=yes | verified=True | lic=OGL v3.0 | cost=
- Ordnance Survey OpenData attribution | use_v1 | commercial=yes | verified=True | lic=OGL v3.0 (OS OpenData licence URL redirects to the OGL) | cost=
- ONS geography products attribution | use_v1 | commercial=yes_with_conditions | verified=True | lic=OGL v3.0 | cost=
- OpenStreetMap / ODbL | use_v1 | commercial=yes_with_conditions | verified=True | lic=Open Database License 1.0 | cost=
- TfL open data terms | use_v1 | commercial=yes_with_conditions | verified=True | lic=Based on OGL v2.0 with TfL amendments | cost=