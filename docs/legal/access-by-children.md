# Children, and a website that looks like a game

**Draft, for the founder to review. Not legal advice.** Written on 26 September 2026 from five pages read that day and from this repository, by someone who is not a lawyer. Nobody qualified has read it. It is the page that task 14 of [the launch checklist](data-protection-checklist.md) asks for. The founder decided that day that the website's new look stands, and asked for the reasoning in writing. When this page was written the look was still being built, and no visitor had seen it. **Brought up to date later that day**: the founder walked the website, and asked that the rabbit moves all the time, and that the first page says Burro is for a person who is buying, renting or just visiting. Section 3 says what changed of the rabbit, and what it adds to the weighing, and the last row of section 2 what the page now says of itself. No conclusion of this page was changed for either: each is the founder's to draw. **Brought up to date again that evening**, once the founder had walked the website a second time: the rabbit has no button, and nothing stops him but a person's own system, a first search waits a few seconds so that he is seen to hop, he is on every page, Burro asks nothing, and a search may be a visit. Section 3 says what changed and what each adds to the weighing. No conclusion was changed for any of them either. **Brought up to date a third time on 27 September 2026**, once the founder had walked the website a third time: the rabbit hops more slowly and a first search waits longer with him, soil flicks up from his hole, every gauge has a small picture at each end, three groups of the settings have a drawing where they had a plain box, recorded crime among them, and a result holds fewer words than it did. Section 3 says what changed and what each adds to the weighing. No conclusion was changed for any of them. [README.md](README.md) says what a mark means.

## 1. In short

Two rules bear on this. The Children's code of the Information Commissioner's Office (ICO) applies to a service "likely to be accessed by children", where a child is "a person under 18" and likely is "more probable than not". Google's terms forbid a product "directed towards or ... likely to be accessed by individuals under the age of 18", and its model [was turned on](../../deploy/README.md#turning-the-model-on) on the hosted service on 26 September 2026, with its terms accepted by name. **So the promise to Google is made already, and was made before this page was written.**

**The new look is on the regulator's own list of what appeals to children**: "cartoons, animation, music or audio content, incentives for children's participation, digital functionalities such as gamification". Burro the rabbit is a cartoon, he is animated, on the first page of the website and for as long as it is open, and the founder's own words for the touches were "gamified elements". The code says: "If the nature, content or presentation of your service makes you think that children will want to use it, then you should conform to the standards in this code." This page argues with none of that.

It concludes that Burro is not directed towards children, and that it is not likely that more than a few of them use it. **That is not sure. It rests on what Burro is for, and on no evidence of who uses it.** Nobody counts who uses Burro, nothing stands between a child and the website, some people under 18 have a use for it, and the bar is low: "more than a de minimis or insignificant number".

## 2. The ICO's list, factor by factor

The factors are the ICO's own, shortened. A number is a section of the [terms of use](terms-of-use.md) or of the [privacy notice](privacy-notice.md).

| Factor | What is known of Burro | Where that is held | Weighs towards children, or away |
|---|---|---|---|
| **Actual evidence** | | | |
| Whether children can access it, and what keeps them out | They can, and nothing does. It is an open website: no account, no check of age, and no statement of age on any page. A statement would keep no child out: "Self-declaration will not be sufficient to demonstrate that children cannot access your service". **Since 26 September 2026 there are accounts, which are off until they are turned on.** Where they are on, a person says that they are 18 or over before an account is made. It is the one statement of age on the website, it stands before an account and before nothing else, and section 8 says what it adds | Terms, 1 and 6. [README.md](README.md), risk 13 | Towards |
| The number and proportion of child users | Not known, and Burro cannot count them: no account, no cookie, no analytics. With accounts on it can count accounts, and cannot count the children among them, nor anybody who searches without one: section 8. **So the founder cannot show that few children use Burro, only that nothing has shown that many do** | [ADR 0005](../adr/0005-raw-prompts-are-never-stored.md), [ADR 0011](../adr/0011-nothing-is-kept-for-a-search.md). Notice, 2 | Neither way |
| Research of its own, and what is seen of how people use it | None. Nobody has looked in the log for what the ICO names: "peaks in access, for example after school and during the school holidays" | Notice, 8 | Neither way |
| Advertising targeted at children | None. The website loads nothing from another company, and no advertisement is in its code. None for Burro is known of | Notice, 2 | Away |
| Complaints about children's access | None, and nowhere to send one yet. The statement of accessibility said so until 26 September 2026, when it went. No page says it now | Task 11, which asks for an address | Neither way |
| **Other evidence** | | | |
| Content, design and activities | Rents and prices, journeys to work, what a neighbourhood is like. Nothing to play. Those who rent or buy are nearly all adults. But one of 16 or 17 who is to study or work in London is a child under both rules, and a household that is choosing often has children in it: an example on the search page asks for "good primary schools". The design is section 3 | `apps/web/src/content/search.ts` | Away, but for the look |
| Other research, and news | None was found. No web search was made | Nowhere | Neither way |
| Whether children like and use similar services | By what it does, Burro is like a website for finding a home. By its look it is like a video game, and children like those. Nothing was read for either | Nowhere | Towards, by its look |
| The business model | Free, with nothing sold and no revenue. A paid tier is planned and not built. Accounts are built, and are off until they are turned on: they are free, and keep a search. The plan names no advertising. Nothing gains from how long a person stays | [The plan](../PLAN.md), 3, 4, 13 and 15 | Away |
| How it is described and promoted | Headed "Find your area" since 26 September 2026, where it was headed "Decide where to live". Under the heading it says who it is for: a person who is buying, renting or just visiting. A visitor may be of any age, which a person who rents or buys seldom is. No promotion is known of, and none was looked for: no domain, and no page may be indexed while the data is a preview. What was said of Burro elsewhere is not known here. Once the data is finished, the plan means the page of each area to be found through a search engine. Since the evening of 26 September 2026 a search may itself be a visit: "Visiting" stands beside renting and buying, and a sentence that says a person is visiting is read as one | `apps/web/src/content/search.ts`. `apps/web/src/lib/indexing.ts`. The plan, 13. [ADR 0041](../adr/0041-a-search-may-be-a-visit.md) | Away, until a page may be indexed, and less so since it names a visitor |

**Burro stands between two of the ICO's examples.** A small business need take no action, because "the content, design features and activities on the site are not appealing to children". A video game whose terms say 18 finds that children are likely to play it: it has "cartoon animations", and it is "one of the top played games in the UK". Burro has the design of the game, and no evidence of who uses it. A third example stays outside the code though it "may appeal to underage users", because it checks each person's age. Burro checks nothing.

## 3. The look, part by part

| Part of the look | On the ICO's list as | What holds it |
|---|---|---|
| Burro, a rabbit with a name | A cartoon | He is drawn once on every page: beside the heading of the first page, where he hops, and on every other page in the name board, or over the foot of the page on a narrow screen. He is beside no result and no area, and not on the map |
| He moves all the time, wherever he is drawn: an ear, his nose, a blink, a shuffle | Animation | Nothing on the page stops him: the button that did went on the evening of 26 September 2026. He is still where a person's system asks for less movement, and nowhere else. One line stills him everywhere. Nothing else on a page moves because he does, and he makes no sound |
| He hops in and out of his hole, and soil flicks up from it | Animation | Only while a person waits for a first answer: while a search is read, and while a first ranking that a press asked for is worked out. Since the evening of 26 September 2026 a first search is held, however soon the answer is in, so that he is seen: for two rounds of his hop at first, which was two seconds, and since 27 September 2026 for three rounds of a slower hop, which is three seconds and three quarters. Not where a person's system asks for less movement, where he sits still, no soil is drawn and nothing is added to the wait. The soil stays inside his box, and nothing on the page moves because of it |
| A meadow, small drawings, a pixel typeface for names | Cartoons | Every sentence and every figure is set plainly for reading |
| A small picture at each end of every gauge, since 27 September 2026: a house and a block of flats, one young tree and two trees | Cartoons | Each says what an end of a gauge is. On a result it stands for the name of the end, which is not written there, and the key to the drawings says what each means. None pictures a person: a vibe that counts who lived somewhere is a page of a register. None says that an end is good or bad, and none is a picture of any place |
| A drawing for recorded crime, since 27 September 2026 | Cartoons | A sheet on its board, with a tally on it: a count that was written down. It is no warning and pictures nothing to fear, and nothing of it is red |
| Pennants, gauges, buttons that press, chips that drop into place. Until the evening of 26 September 2026 a dialogue box too, which went when Burro came to ask nothing | Gamification | **Nothing is won.** No points, stars, levels, prizes or streaks, and nothing to collect |
| Sound, people, rewards | Audio, "presence of children", incentives | There are none |

`[FOUNDER: the last column is what the look was held to as it was built. As the look was finished it was written into a decision record,` [ADR 0033](../adr/0033-the-website-looks-like-the-map-of-a-gentle-game.md)`, which names the test that holds each row and says what no test holds: that nothing on a page is a prize, a score or a level, and that the rabbit is on no result, map or comparison. Those are promises still. One row is in doubt: the rabbit's head is the icon of the website, which a browser shows on every page. The record says so, and whether it stands is yours to say. The record was amended on 26 September 2026, after you walked the website: it says that he moves all the time, that he can be stopped, and what holds each. A way to draw him in the name board of every page was built with it and left off. It was turned on as the website was mended that afternoon, so he is on every page, the page of an area among them, and the first row of the table now says so. The record was amended again that evening, after you walked the website a second time: he has no button, and a first search waits a few seconds with him. It was amended a third time on 27 September 2026, after you walked the website a third time: every gauge has a picture at each end, recorded crime has a drawing, and the hop is slower and longer and throws soil. It says what a picture of an end may never be, and that no test holds it.]`

**What changed on 26 September 2026, and what it adds.** When this page was written Burro moved only while a person waited for a first answer, which is a few seconds, and sat still everywhere else. The founder walked the website and asked for more: "the burrow bunnny should always be animated, ear twitching, sniffins, shuffling etc, he should add some movement and whimsey to the page." So he now moves on the first page of the website from the moment it opens, with nothing typed and nothing pressed, and where he stands to ask.

| What it adds to the weighing | Towards children, or away |
|---|---|
| Animation is on the regulator's list by name. It was seen for seconds, by a person who had searched. It is now the first thing that moves on the first page, for as long as the page is open | Towards |
| The movement is there to be looked at. The founder's words for it are "movement and whimsey". Before, each movement had a reason a person could name: they were waiting, or had pressed | Towards |
| A child need not search to see him move, though he hops in and out of his hole only while a search is worked out. What is watched goes nowhere, and what is typed may go to a model | Away, a little, from the reason to type that is said below |
| He can be stopped, by a button that a keyboard reaches and a screen reader names, and he is still where a system asks for less movement | Neither way. It is what the guidelines on accessibility ask of whatever moves without end, and it keeps no child out |
| Nothing is won by watching him, he makes no sound, and he is no person | Neither way. It was so before |

**What changed that evening, and what it adds.** The founder walked the website a second time, and wrote of the rabbit: "remove the pause button for the rabbit, for accessibility we will rely on users having motion turned off in the browser", and "even if not needed, create a few seconds load time to allow the bunny jumping into a hole animation to appear and take center stage". They asked too that Burro asks nothing, that a search may be a visit, and that the words under the box go.

| What it adds to the weighing | Towards children, or away |
|---|---|
| He cannot be stopped by a person. A person who does not want him to move sets their own system to ask for less movement, and no page says that they can | Neither way, of who comes: the button kept no child out, and its going lets none in. It is a matter of who can use the website, which [ADR 0042](../adr/0042-the-website-makes-no-claim-of-a-standard-of-accessibility.md) weighs |
| A first search waits so that he is seen to hop: two seconds, as it was built that evening. Until then he hopped for as long as the service took, which was often a few frames | Towards. The animation that a search brings is now sure to be seen, and is shown on purpose: the founder's words for it are "take center stage". It is the one thing the look gives a child as a reason to search |
| He is on every page, since the website was mended that afternoon | Towards. He was on the search page alone. A child now meets him on the page of an area and on the pages that explain |
| Burro asks nothing. The dialogue box is met nowhere, with the rabbit on his hind legs beside it and the carrot beside each of its choices. A carrot lies still beside the choice in hand in a list of examples or of places | Away, a little. One touch of a game went |
| A search may be a visit | Towards, a little, as the last row of section 2 says of the first page: a visitor may be of any age |
| Nothing beside the box says who reads what is typed, or advises that nothing private is typed | Neither way, of who comes. It bears on what follows if the conclusion is wrong: with a model on, what a child types may go to Google, and nothing where they type says so |

**What changed after the third walk, and what it adds.** The founder walked the website a third time, late on 26 September 2026, and wrote of the rabbit: "slow the hole hopping animation down a bit and make it last a tad longer, make soil flick up as it burros". Of the gauges: "where a gauge may exist, ensure they have a opposing icons for each side of the gauge". Of what was not drawn: "Create visuals for brands near by, air and noise and recorded crime". And of a result, three times over, that it held too much detail: the words under a gauge, the sentences that said why an area fits and the key of every source went from it.

| What it adds to the weighing | Towards children, or away |
|---|---|
| A first search waits longer with the rabbit, and he hops more slowly: three seconds and three quarters, where it was two seconds | Towards. The animation that a search brings is seen for longer, and is shown on purpose. It is still the one thing the look gives a child as a reason to search |
| Soil flicks up from his hole as he goes down and as he comes up | Towards, a little. It is more animation, and it makes more of a cartoon of him. It is inside his box, it is seen only while he hops, and it makes no sound |
| Every gauge has a small picture at each end, wherever a gauge is drawn: on a result, on the page of an area, in a comparison, in the settings and on the page of vibes | Towards. There are many more small drawings on the pages a person reads, and cartoons are on the regulator's list by name. None pictures a person, and none is a thing to win |
| A result holds a name, a gauge and a drawing for each thing that was asked for, and one sentence. The sentences that said why an area fits went, with the words under each gauge | Towards. Section 4 leans on what a child finds who comes for the rabbit: "a form about rent, and nothing to play". A page of results is now more picture and less form than it was when that was written. It is still nothing to play: nothing is won, and no gauge is a score |
| Recorded crime has a drawing, and so has a vibe that counts it | Neither way, of who comes. It bears on what a child who came is shown. The drawing is a tally on a sheet, and the end of the gauge is a works with its chimney: nothing frightens, nothing is red, and nothing says that a place is safe or is not |
| What an area gives up is drawn with a pair of scales, where it had a red arrow | Neither way |
| Nothing is won by any of it, nothing makes a sound, and nothing pictures a person | Neither way. It was so before |

**The founder chose it knowing the list.** When the look was chosen the founder was told that the regulator names cartoons, animation and gamification, decided that the look stands, and asked for this page. They said of what a regulation may ask: "we can remove things or downplay things in relation to regulation later if needed". They asked for a rabbit who always moves after that, with the website in front of them. So he was built to move, and built so that one line stills him: [the design of the look](../design/look.md), section 3, has it first on its list.

**The look still gives a child one reason to type.** Burro hops in and out of his hole only while a person waits for a first answer, so a way to see him hop is to search, and with a model on what is typed may go to Google. Since that evening he is seen to hop for a few seconds, whatever is typed, and since 27 September 2026 for longer, with soil. As the look was finished a press came to show him too: a word of the shelf, or the settings ranked as they stand, asks for a first ranking, and sends nothing that was typed.

All of it makes Burro no game. None of it makes Burro look like none: a child sees a rabbit on a meadow.

## 4. What is concluded, and how sure

| Question | This draft's answer | How sure |
|---|---|---|
| Is Burro directed towards people under 18? | No. What it is for, what it asks and how it is described are for a person choosing a home | Fairly. The look alone points the other way |
| As it stands, is it likely that more than a few use it? | No. It has no domain, no page of it may be indexed, and no record says that anyone was told of it | An inference, with no count behind it |
| And once it is launched, in the new look? | This draft leans to no: a child who comes for the rabbit finds a form about rent, and nothing to play. Against it stand pages found through a search engine, people under 18 with a use for Burro, and a rabbit who moves on the first page and hops when a person searches. The lean was written before he moved all the time, before he was on every page, before a first search waited with him, and before a result came to hold more drawings and fewer sentences. Whether it stands is the founder's to say | **Not sure. It is a lean, with no evidence behind it, and an officer of the ICO could lean the other way** |

If it is wrong, the two rules pull apart. The ICO gives two ways on: "apply the principles of the code to all users in a risk-based and proportionate way; or apply appropriate age assurance measures to restrict access by under 18s ... if it would not be appropriate for them to do so". Age assurance is checking or estimating a person's age. Nothing in Burro is unfit for a child, so this draft reads the first way, to meet the code for everyone, as the ICO's for Burro. Google's terms leave only the second: until children are kept out, the model goes off. With the model off, Burro keeps nothing of what a child types.

As read, Google's terms give no meaning for their words, so Google may read them more widely than this page does.

## 5. What would change the founder's mind

Burro records nothing of who visits. So each of these is seen only if somebody looks, or somebody writes. Nobody can write yet, for Burro gives no address: task 11.

| What is seen | What is then done |
|---|---|
| A message that says a child uses Burro | Answer it, as task 11 says, and read this page again that week. At a second, from another person, the conclusion is lost |
| A school, a college or a website for the young links to Burro | The conclusion is lost |
| A press piece, a post or a video calls Burro a game | Ask for the word to be put right. If it was made for the young, or reached many people, the conclusion is lost |
| The log shows peaks after school, or in the school holidays | Read this page again that week |
| The iPhone app is on sale under a rating that reads as fit for children | Take it off sale until the rating is raised. Row 6 of section 6 keeps it from happening |
| The look goes onto the website. Burro is given a domain, may be indexed, or is promoted | Read this page again the day before |
| A thing to win or collect, a sound, or a picture of a person is to be added | It waits until this page has been read again |

**When the conclusion is lost**, the model goes off that day, and stays off while children are likely to use Burro: [the guide to deployment](../../deploy/README.md#turning-the-model-on) says how. Then, within a month, one of the ICO's two ways: meet the code for everyone, or put a check of age in front of Burro. To take the game out of the look is not one of them, and would not by itself show that children had gone. Task 17 is answered again too: children are among the ICO's reasons for an impact assessment, and it says no to them today.

## 6. What is the founder's to do, in order

| # | | |
|---|---|---|
| 1 | Read | The ICO's two pages in a browser, with its examples of games and of small websites whole. Then Google's term on age. Then research on who uses websites for finding a home, and games of this look: the ICO names "market research" as what supports a decision, and none was read |
| 2 | Decide | Whether the model stays on, and whether the look goes onto the website, before rows 3 to 5 are done. The model was turned on on 26 September 2026, and no record says that it was turned off. Since that evening nothing where a person types says that a model reads: [ADR 0023](../adr/0023-what-is-typed-goes-as-typed-and-people-are-told.md), as amended |
| 3 | Decide | Whether the conclusions of section 4 are yours, now that the rabbit moves all the time, is on every page, cannot be stopped but by a person's own system and is given some seconds of every first search, in which he throws soil, and now that every gauge has a picture at each end. And the numbers of section 5, which are this draft's. Say here first where Burro has been shown or spoken of, if anywhere: this page cannot know |
| 4 | Decide | The age, which both drafts propose as 18, and whether it is said where a person types. It is a statement and no check |
| 5 | Write | In the terms, section 6, and in the notice, section 16: "Burro is for people aged 18 or over. It is for choosing where to live, and it is not a game." Both say already that Burro asks no age and checks none. The first page says since 26 September 2026 that Burro is for a person who is just visiting too, and since that evening a search may be a visit, so what it is for is yours to word again |
| 6 | Do | Before the app is submitted: "choose Override to Higher Age Rating", and never "Made for Kids". Where an app's terms ask for an age above the rating Apple works out, Apple says "you must override to a rating that adheres to the requirements" |
| 7 | Do | Call Burro a game nowhere, and promote it nowhere that many who see it are under 18 |
| 8 | Do | Have section 3 written into a decision record, with tests, and name both here. Say there whether the rabbit is the icon of the website. The record was written as the look was finished, amended once the rabbit was to move all the time, amended again once his button was to go, and a third time once every gauge was to have its pictures. Section 3 names it: what is left is to read it, to say whether the icon stands, and to say whether he is drawn in the name board of every page |
| 9 | Do | Keep a dated copy of this page as you accept it, with your name, outside this repository. Read it again with task 19 |

## 7. What was read, and what was not

Each page was read on 26 September 2026, through a reader that extracts of a page and not the page itself. A quoted sentence may differ from the source by a word. Check the wording at the address before relying on it. Apple's two pages were read as they are served as well, and what is quoted of them is there word for word.

| Page | Address | Read |
|---|---|---|
| ICO, the Children's code, "Services covered by this code" | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/age-appropriate-design-a-code-of-practice-for-online-services/services-covered-by-this-code/> | Read twice |
| ICO, "'Likely to be accessed' by children – FAQs, list of factors and case studies" | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/likely-to-be-accessed-by-children/> | Read twice. Of its examples, those of games, of small websites and of a website for adults were read whole, and the others in short quotations |
| Google, the terms of the Gemini API, under "Age Requirements" | <https://ai.google.dev/gemini-api/terms> | Read twice |
| Apple, "Set an app age rating" | <https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating/> | Read twice |
| Apple, "Age ratings values and definitions" | <https://developer.apple.com/help/app-store-connect/reference/age-ratings-values-and-definitions/> | Read once |

| Not read | Standing |
|---|---|
| The standards of the code, and the ICO's pages on checking age | What it would take to meet the code is not known. In two of the ICO's examples a game and a small website met it, and had nothing more to do |
| What Google means by "directed towards" and by "likely" | Its terms do not say, as read. This page reads them as the ICO reads its own words. Where its rules are broken Google may limit, suspend or close an account: [the report on Gemini](../research/models/gemini.md), section 8 |
| Which rating Apple would work out for Burro, and what a rating does on a child's phone | Apple works a rating out from what an app contains. That Burro's would be the lowest is an inference |
| The Online Safety Act 2023 | [An earlier report](../research/reports/accounts-compliance.md) reads Burro as outside it |
| Research on who uses websites for finding a home, or games of this look | No web search was made |
| What the other three providers ask about age | [The design of the models](../design/models.md), section 3, has a row for it, which nobody has checked. Its section 10 holds "Adults only" among what is the founder's to decide, with nothing decided |
| Whether a person under 18 may rent or buy a home in their own name | That nearly all who rent or buy are adults, and that many households that move have children in them, are taken as known |

## 8. What accounts add

Written on 26 September 2026, the day the founder asked for accounts. They are built, and they are off until they are turned on ([ADR 0043](../adr/0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md)). Nothing in this section is so of the website while they are off. **No conclusion of this page was changed for it**: each is the founder's to draw, and this section says what there is to weigh.

| What is built | |
|---|---|
| What an account is for | To keep a search. A search, a comparison and a shared link ask for no account, as before, so an account stands between a child and nothing that they could do already |
| What is asked | When an address signs in for the first time, the page asks the person to confirm that they are 18 or over. No account is made until they have |
| What is kept of the answer | The time at which the person confirmed it, with the account. No date of birth and no age |
| What is checked | Nothing |
| What an account holds | An email address, and the searches that were kept: [the privacy notice](privacy-notice.md), section 20 |
| What reaches a language model | What it reached before. A sentence is sent with or without an account, and nothing of an account goes with it |

**What the ICO says of a statement that nothing checks.** Its code calls it self-declaration: "This is where a user simply states their age but does not provide any evidence to confirm it." And of when it will do: "It may be suitable for low risk processing or when used in conjunction with other techniques." The standard it stands under, as read: "Either establish age with a level of certainty that is appropriate to the risks to the rights and freedoms of children that arise from your data processing, or apply the standards in this code to all your users instead." Read on 26 September 2026, at <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/age-appropriate-design-a-code-of-practice-for-online-services/3-age-appropriate-application/>, through a reader that extracts of a page. Section 2 quotes the ICO's other page, on what shows that children cannot reach a service: a statement is not enough for that.

| What accounts add to the weighing | Towards children, or away |
|---|---|
| The website now says, in one place, that it is for people of 18 or over, and a person must answer before they go on. Until now no page said it | Away, a little. It says who Burro is for. It keeps nobody out |
| A child who ticks the box has an account. Burro then holds a child's email address, and whatever they kept, for as long as the account lasts. Before accounts Burro kept nothing of anybody | Neither way, for who is likely to use Burro. **But it is a new thing to get wrong**: what was nothing held of a child is now something held |
| Whether keeping a search is "low risk processing", in the ICO's words, is not said on the page read. What is kept is where a person must get to each day. It is shown to the person and to nobody else, is sold to nobody, and no conclusion is drawn from it | Not known. It is the founder's to weigh, with task 17 |
| An account gives a reason to come back. Nothing is won by it, nothing is counted, and no email is sent but the one that holds a link to sign in | Neither way. Section 3 holds that nothing is won |
| Google's term is about who is likely to use Burro. A model is reached with or without an account, so the box that is ticked stands before nothing that Google's term is about | Neither way |
| Accounts can be counted. Children among them cannot | Neither way. The row of section 2 on how many children use Burro stands |

**What is the founder's to do, for accounts.** Each is before accounts are turned on, and step L of [the launch checklist](data-protection-checklist.md), under "Before accounts are turned on", points here.

| # | | |
|---|---|---|
| 1 | Decide | Whether a box that is ticked is enough for an account, given what an account holds. The other choices are to check age, which the ICO's pages on it would have to be read for and which nothing here builds, or to hold accounts to the standards of the code for everybody |
| 2 | Decide | What is done when somebody says that an account is a child's. This page proposes: the account is deleted, the person who wrote is told so, and the message is one of those that section 5 counts |
| 3 | Decide | The words beside the box. They say what is asked and nothing else. They do not say why, and they do not speak to a child |
| 4 | Read | The ICO's pages on checking age, which section 7 lists as not read |
| 5 | Do | Read section 4 again with accounts in mind, and say whether its conclusions are still yours. Task 14 asks for a page that is the founder's own |

