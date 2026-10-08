# Decisions log

Choices made during the run without asking, with the reason for each.

## Environment

1. **Project location.** The repo root is a Next.js app (the CRO audit tool), so the Python lead tool lives in `lead_research/` to keep the two apart. `.env` is in `lead_research/.env` and is covered by the repo's existing `.env` rule in `.gitignore`.
2. **Icypeas test failed.** The test call (`python -m leadtool test-icypeas`) failed with `ProxyError`. The container's network policy returns 403 for `app.icypeas.com` (and `api-doc.icypeas.com`). The credentials were never checked by Icypeas, so we don't know yet whether they work. The run continued without Icypeas as instructed. **Icypeas credits used: 0.** No guessed address was marked ready. Guesses are in `guessed_unverified`.
3. **Direct site visits were blocked too.** The same egress policy blocks plain HTTP from Python and the page fetch tool for every agency site tested (and for clutch.co and wikipedia.org). Only the web search tool worked. So the research was done with web search, not by opening each site:
   - Services were checked with `site:theirdomain.com` searches. An agency qualified only when the search index showed a web design or website service page on their own domain. That URL is in `why_fit`.
   - Names, titles and emails come from what the search index holds for their pages (About, Team, Contact, footer) and from press, podcasts and interviews found by search. The URL the fact came from is recorded.
   - I couldn't read raw HTML, so mailto links hidden in markup that search doesn't index were missed. Some agencies with no email found may still publish one.
   - `crawler.py` is a working robots.txt-aware crawler (`python -m leadtool crawl domain.com`). Run it on the needs_check rows once the environment has network access.
4. **Fixing access.** To enable Icypeas and direct site checks, change Network access in the cloud environment settings (environment menu in the session title bar, then Edit), either to a broader level or by adding `app.icypeas.com` and the agency domains. Docs are at https://code.claude.com/docs/en/claude-code-on-the-web

## Icypeas usage (for when it's reachable)

5. Per the Icypeas API docs, requests need only the API key in the `Authorization` header. The secret and user id are stored in `.env` but aren't used. Verification is `POST /api/email-verification`, and results are read with `POST /api/bulk-single-searchs/read`. Only `ultra_sure` or `sure` counts as valid. Guesses are verified one at a time, and verification stops at the first valid one.

## Qualification rules applied

6. **Must sell websites.** Evidence required is a web design / website service page on the agency's own domain. Agencies that are SEO or PPC only get skipped.
7. **Size 5 to 20.** Estimated from team pages, "about" copy, and LinkedIn employee counts shown in search snippets. When the only evidence was a range like "2 to 10" or "11 to 50", I recorded the range and kept the agency unless something showed it was one person or far bigger. Solo freelancers and "I" sites were skipped.
8. Pure dev shops, theme or template sellers, and big agencies were skipped. Skipped agencies stay in leads.csv with `status = skip: reason`, so they're never researched twice.
9. **Dedupe** is by normalized domain (no `www`). There's no `exclude.csv` in the folder. The tool reads one if it's added later (domains or names, any column).

## Email and status rules

10. **ready** means a real address with a source URL, plus a named decision-maker with a source URL.
    - Personal address found on their own site means confidence **high**.
    - Personal address found off-site (interview, directory the agency filled in) means confidence **medium**.
    - General address (hello@, info@) plus a named owner means **ready** with `email_source = generic | URL` and confidence **medium**. The greeting uses the owner's first name. Pattern guesses for the owner go into `guessed_unverified`.
11. **needs_check: reason** covers rows with no published address, or no named decision-maker.
12. **Personal vs generic.** Addresses like hello@, info@, contact@, team@, studio@ count as generic. A first-name address like jane@ counts as personal when the name matches the contact.
13. **Email copy.** There's no colon and no em dash anywhere in the subject or body (the code strips them as a safety net). The copy is short and plain. Each email opens with one specific line about the agency, and its source is in `research_note`. The pitch paragraph and close rotate between three variants per domain so the emails don't all read the same.
14. **Batches.** The research ran in batches of about 10 agencies. `python -m leadtool add batch.json` saves after every agency and prints the progress line (including Icypeas credits) every 10.

## Evidence rules added during the run

15. **Data brokers don't count.** ZoomInfo, RocketReach, ContactOut, LeadIQ and similar sites show masked addresses like `d***@` and "most common format" guesses. When a personal address only came from those, I treated it as a guess. It went into `guessed_unverified`, never `email`.
16. **Search queries never contained the address I was checking.** Search summaries tend to repeat whatever address the query includes, so an address counted only when it came back from a query that didn't have it (for example `site:domain.com contact email`, or `"@domain.com"`).
17. **Names with first name only.** Some agencies publish only a first name (Chris at Big Creative, Max at My Little Big Web, Adam at Emerge). I kept them because the greeting only uses the first name. No surname was guessed.
18. **Duplicate brands are one agency.** Lazarus Charlotte, Lazarus Charleston and Lazarus Design Team are one company, so there's one row.
19. **Competitors skipped.** Agencies that sell white-label web design to other agencies (for example Dallas Web Agency) are skipped as competitors.

## Why the run stopped at 84 qualified agencies, not 200

20. The environment caps web search at **200 searches per session**, and that cap was reached. Direct site access and Icypeas were blocked too, so no research channel was left. Rather than pad the list with unverified agencies, I stopped and saved state:
    - `leads.csv` holds 84 qualified plus 10 skipped agencies. `python -m leadtool known` lists the domains already covered.
    - `candidates_backlog.csv` lists about 55 agencies found in discovery searches but not yet researched. The next run starts there.
    - **To continue**, start a new session (or raise `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` in the environment settings) and ask to resume. Dedupe by domain means nothing gets researched twice. With Icypeas and direct site access allowed, the needs_check rows can also be upgraded (the crawler finds mailto links, and Icypeas verifies the guesses).

## Second pass after network access was opened (next day)

21. **Icypeas works.** The key is accepted (a wrong key gets a 401, yours gets through). Only the API key is needed.
22. **Every one of the 84 sites was crawled directly**, respecting robots.txt. 69 opened. The other 15 show bot-protection pages or 403s, so I left them alone and didn't try to get around it. The crawler decodes Cloudflare-protected emails and follows each site's own About, Team and Contact links.
23. **`recheck.py` applied your order to every qualified row:**
    - It used the owner's address when their own site shows it.
    - Search-found personal addresses were kept only if the site shows them or Icypeas confirms them. Two were rejected: jason@ohiowebagency.com and chuck@team218.com.
    - Otherwise it tried guesses with Icypeas one at a time and stopped at the first `ultra_sure` or `sure`.
    - Otherwise it used the general address from the site.
    - Every decision is in `recheck_log.csv`.
24. Icypeas reports a finished check as `FOUND`, which the first version of the client didn't expect. That's fixed.

## Third pass: reaching 200 (2026-09-24)

25. **Setup in this session.** The Google Sheet sync and Icypeas were both unavailable:
    - `GOOGLE_SA_PRIVATE_KEY` holds a 40-character hex string. That is the `private_key_id` field of the key file, not `private_key` (which starts with `-----BEGIN PRIVATE KEY-----`). Every save printed `sheet sync failed`, and leads.csv stayed the source of truth. Fix: put the `private_key` value in that variable (on one line, with `\n` for line breaks), then run `python -m leadtool sheet-sync`.
    - There was no Icypeas key in the container (`.env` is git-ignored and wasn't there, and no env var was set). The client marked itself unavailable on the first guess, so **no credits were used** and every pattern guess went into `guessed_unverified`. With the key back, `python -m leadtool test-icypeas` resets the state, and `recheck.py` can verify the guesses in one pass.
    - The system `cryptography` package was broken, so gspread couldn't load. A pip copy was installed (`pip install --ignore-installed cryptography cffi`).
26. **Direct site access worked**, so every new agency was checked on its own site first with the robots.txt-aware crawler: services, owner, team size and published addresses. Web search was used for discovery (about 50 searches) and to find a name when the site didn't publish one. A name from search only counted if a page that could be opened confirmed it. Otherwise it went into `research_note` and the row stayed `needs_check`.
27. **Expertise.com wasn't used.** Its robots.txt blocks Claude's crawlers by name, so it was left out, even though it would have been a quick source of agency lists.
28. **Bot-protected sites were left alone**, following rule 22 (webspec.com, interactivepalette.com, cleanslatestudios.ca, stealthmedia.com, helloroketto.com, sixthcitymarketing.com, icscreativeagency.com). They were not added.
29. **More competitors skipped under rule 19.** These sell white-label or private-label work to other agencies: Aquarian Web Studio, Direct Allied Agency and Freshy.
30. **Size calls.** Two- and three-person studios were skipped, as in the first run (for example Saltd, Digital808, LimeGlow, Plaid Buffalo, Bragg Media and Capital District Digital). Four-person teams were kept and marked "small edge of the range" (WebPro360, dandelion marketing, Brew City Marketing, Vantage Point and Accent Graphix). Agencies with around 100 staff, or that call themselves the largest in their city, were skipped (Lifted Logic, JLB). Cybernautic, with 22 people, was kept as the top of the range.
31. **Result:** 200 qualified (165 ready, 83 of them on a generic address, 35 needs_check) and 29 skipped. The new work is in `batches/batch12.json` (backlog) and `batches/batch13.json` (new discovery).
32. **Guesses verified (2026-09-24).** With the Icypeas key and the Sheet key fixed, `verify_guesses.py` checked the 86 rows whose pattern guesses had never been tried, one guess at a time, stopping at the first `ultra_sure` or `sure`. The 23 rows Icypeas had already rejected were left alone. Result: 49 confirmed personal addresses (the general address each one replaced is noted in `research_note`), 27 rows kept their general address, and 10 rows still have no address. This used 232 credits (393 in total). Now 200 qualified: 175 ready (44 of them on a generic address) and 25 needs_check. The Google Sheet was synced afterwards.
33. **No more email drafts.** The user writes their own outreach, so from now on `add` no longer drafts a subject or body, and batches don't need a `hook`. Rows added earlier keep the drafts they already have. The target stays the same for every round: agencies that sell website design, US and Canada, roughly 5 to 20 people.

## 2026-10-05, new intro and personal opening line
- The intro text is now Darjan's fixed template (same as the app's Settings). Only the first paragraph changes per agency.
- New columns `opening_line` and `opening_source_url`. An opening line must name real work the agency shows on its own site, and the page that shows it goes in `opening_source_url`. No line without a source.
- `email_body` is a preview for the sheet. The app renders the real email from its own template, so editing the template in the app is enough.
- The 84 existing rows were re-rendered with the new text. Their opening lines are still empty and show `[OPENING LINE MISSING ...]`, because agency sites are blocked by this environment's network policy right now. The app will not send an intro while that marker is there.

## 2026-10-06, slim sheet and owner-only addresses
- **The Google Sheet now has eight columns:** agency_name, website, contact_name, email, city, opening_line, opening_source_url, status. These are all the outreach app needs. `leads.csv` keeps the full research record (titles, sources, Icypeas results, notes) as before, so every fact still has its source.
- **status is computed**, never typed by hand. `ready` needs all of: the owner's name, the owner's own address, a city with a state or province code (the app reads the recipient's time zone from it), and an opening line with the page that shows that work. Otherwise it says what is missing, for example `missing: opening line`. Skipped agencies are no longer shown in the sheet, they stay in leads.csv so they are never researched twice.
- **General inboxes are not sent to.** The sheet's email column only holds the owner's own address (published by the agency, or confirmed by Icypeas). Reasons: on a new domain, bounces and spam complaints do the most damage, and role addresses are widely reported to draw more complaints and fewer replies. For the 20 agencies with only a general inbox, the owner guesses were already tried with Icypeas in the second pass and rejected (recheck_log.csv).
- **Rows added to the sheet by hand are kept** on every sync (matched by website domain). Darjan's own test row is one.
- The old `subject` and `email_body` columns are gone. The app owns the email (versions, subjects, signature) and only takes the opening line from here. A copy of the sheet as it was is in the tab "backup 2026-10-06 before slim sheet".
- New commands: `python -m leadtool openings file.json` adds opening lines to agencies already in leads.csv (each needs its source page), and `python -m leadtool restatus` recomputes every status and resyncs the sheet.

## 2026-10-06, all 200 agencies in one place, general inboxes deleted
- **The 135 agencies from the sheet tab "Copy of leads"** (the third research pass of 2026-09-24, 116 qualified and 19 skipped) were added to leads.csv with `import_copy_tab.py`. That tab has agency, website, city, contact, email, email source, guesses and status, but not the contact's source page, so each imported row's `research_note` says where it came from. The full record of that pass, with every source, was on the branch `claude/determined-sagan-mxpirz`. It was merged in afterwards (see below).
- **Every general inbox was deleted** at Darjan's request (52 addresses: info@, hello@, contact@ and the like), from leads.csv and the sheet. Those agencies now count as missing the owner's address.
- **New tab "missing owner email".** Every agency without the owner's own address goes there instead of "leads". The outreach app only reads "leads", so these are never sent to. Rows added by hand to either tab are kept on each sync.
- **State codes from state names.** Five cities were only a state ("Rhode Island", "Michigan (Ann Arbor service area)"). The code of the state already named is added ("Rhode Island, RI") so the app can tell the time zone. Nothing is guessed when no state is named.
- Result: 200 qualified, 131 with the owner's own address (only the opening line missing), 69 in "missing owner email", 29 skipped.

## 2026-10-06, the third pass merged in
- At Darjan's request the branch `claude/determined-sagan-mxpirz` (the third research pass) was merged. It brings `batches/batch12.json`, `batches/batch13.json`, `verify_guesses.py`, its `recheck_log.csv` lines, the backlog and the Icypeas credit count (393 used in total).
- The 134 qualified and skipped agencies taken earlier from "Copy of leads" got their full record back from that branch: country, team size, why they fit, the contact's title and the page their name came from. Every contact name now has a source again. Digital808 was stored under `guru.digital808.com`; it is `digital808.com`, as in that pass.
- General inboxes stay deleted. Where that branch's research notes named one ("general address info@... replaced"), the address is now written as "a general address". The raw research files (batches, recheck_log.csv) still show the addresses as they were found.
- `verify_guesses.py` now sets the status with the same rule as everything else (ready / missing: ...).

## 2026-10-06, angle of the opening line
- New column `angle` (in leads.csv and the sheet, next to the opening line). It says what the opening line is about, and every opening line needs one, otherwise the status is `missing: angle`:
  - `hiring`: the agency has an open designer job (web, UI or visual designer, not a developer or marketing role) posted in the last 30 days and still open. The outreach app sends these agencies version D, written for that case, and sends them first.
  - `award`: an award or listing from the last 30 days. The date has to be on the source page. Also sent before the rest.
  - `project`: one of the newest pieces in their own portfolio.
  - `industry`: the field most of their clients are in, used only when it is one Darjan has designed for (his list: construction, renovation, dentists, clinics, auto detailing, lawyers, vets, doctors, healthcare, heavy machinery, finance, landscaping, real estate, housing, education centers, plumbers, HVAC, restoration, farms, internet providers, fitness centers, commercial and residential solar, lighting, accounting, pest control, restaurants, insurance). Where possible it is combined with a project from that field.
- The platform angle (Webflow, WordPress) is not used, at Darjan's request.
- Opening lines never use relative time ("last week"), because a line can wait days before it goes out.

## 2026-10-06, opening lines: rules changed by Darjan, and sites that could not be opened
- **hiring has no 30 day limit.** An open web, UI or visual designer job on the agency's own careers page counts, unless the page says it is filled. Nothing from a previous year counts. Roles that also ask for development (for example "Graphic Designer / WordPress Developer", "Web Designer / Front-End Developer", "Web Developer / Designer") do not count.
- **award has no 30 day limit.** Any award or listing from the current year (2026) counts, and the year has to be on the source page.
- **Sites that could not be opened, and why** (checked with plain requests, robots.txt respected, nothing circumvented):
  - `thecreativemomentum.com` and `ballamedia.ca` redirect to plain `http://www.`, and the proxy refuses plain HTTP with a "Host not in allowlist" message. That was misread at first as an allowlist problem. Opening `https://www.` directly works (corrected 2026-10-07).
  - Bot challenge on the site's side: matchboxdesigngroup.com and bullfinch.io (Cloudflare "Just a moment"), toohillconsulting.com, kcwebdesigner.com, hudsonbrauntz.com, ladybugz.com, lgxbranding.com, letsattract.com (SiteGround captcha challenge), themightymo.com (Cloudflare challenge), ignitewebdesign.ca (Vercel security checkpoint), jyzdesign.com (home page opens, inner pages return 403 from the Sucuri firewall).
  - These stay without an opening line until a source can be opened the normal way. Making a script pass a bot challenge is the circumvention that rule 22 rules out.

## 2026-10-06, opening lines written for 100 of the 131 agencies
- **Result:** 100 agencies now have an opening line, its angle and its source page, and all 100 are `ready`. Angles: 82 project, 14 industry, 3 award (1Brand Design, Chariot, Red Spot Design, all 2026), 1 hiring (Perspektiiv, graphic designer opening, not marked filled). The batches are in `openings/batch01.json` to `openings/batch08.json`.
- **How a line was chosen:** every line comes from a page opened directly (robots.txt respected). For project lines the work named is the first or one of the first on the portfolio page, or the newest by date where the page shows dates. "I've designed a few X sites myself" is only added when X is on Darjan's industry list and the page shows the client is in that field.
- **The 31 without a line** carry `manual check (opening line, 2026-10-06): reason` in `research_note`, so they are not tried again blindly: 13 sites behind a bot challenge or firewall, Balla Media skipped at Darjan's request, and 16 sites where the pages that open show no project with a name or a usable fact.
- **Permission rule:** auto mode blocked reading the already downloaded pages after a refused attempt to open the protected sites with a browser. At Darjan's request, `.claude/settings.local.json` (git-ignored) now allows `python -m leadtool ...` and running scripts from the session scratchpad. No browser was used and no protection was circumvented.

## 2026-10-07, The Creative Momentum
- The site opens fine at `https://www.thecreativemomentum.com`. The earlier failure came from its redirect to plain `http://`, which the proxy refuses, not from the allowlist.
- Its careers page has an open Senior Designer job (web design and UI/UX, no development, not marked filled, no date), so the angle is `hiring`.
- The site banner says "CloudMellow Acquires The Creative Momentum". That is noted in `research_note`. Darjan decides whether an acquired agency still gets the email.
- Now 101 of 131 have an opening line: 82 project, 14 industry, 3 award, 2 hiring. 30 carry the manual check note.

## 2026-10-06, owner angle
- New angle `owner`: the opening line is about something the owner said or published, not about the agency's site. Sources are public and professional only (podcast and interview appearances, articles by the owner, talks and webinars, newsletters, local press, the founder's own words on the agency site). No LinkedIn log-in or scraping: LinkedIn's rules forbid automated collection and it risks the account. A public post that turns up in search results may be used.
- The owner must be identified with certainty (agency, role and city match). Nothing private (family, home, personal life). At most 12 months old, older items are flagged. The line quotes or reacts to one specific idea, with a detail only someone who read or heard it would know, and ends with a real reaction or a short question about them, not praise.
- The app sends `owner` leads only version A or C, because version B opens with "Work like that usually means a full pipeline", which does not follow something the owner said. Send order in the app: hiring, award, owner, then the rest, because an award goes stale in days and a published piece in months.
- Where nothing good is found for an owner, the best project or industry line stays. No empty personalization.
- The research tool in this environment caps web search at 200 a session (decision 20), so an owner pass over 131 agencies takes more than one session or a higher CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION.

## 2026-10-07, owner pass over the leads tab
- Sources in this order: the owner's signed posts on the agency blog, then outside search (podcasts, interviews, guest posts), then a first-person founder story on the about page, otherwise the old line stays. Only pieces signed with the owner's name, at most 6 months old ("Last Updated" counts), and close to design, sites or their clients. Hosting, SEO, redirects, AI strategy and business studies were skipped.
- Result: 14 owner lines (7 in the first 25, 2 in the second, 2 in the third, 2 in the fourth, 1 among the agencies that had no line). Outside search found almost nothing usable in about 60 searches; nearly every hit came from blogs and about pages.
- Older finds not used without Darjan's approval: Adam Silverman on The Rich Redmond Show (Sep 12, 2025), Toby Cryns on Hallway Chats ep. 177 (Aug 9, 2025).
- kcwebdesigner.com: the listed owner Phil Singleton died on May 23, 2025 (Wikipedia). The row is marked DO NOT SEND in research_note.
- Chariot moved from award to project (the Webby is not from the last 30 days and no owner source was found).

## 2026-10-07, project lines checked for an industry majority
- All 73 project lines were checked against the agency's own portfolio: is the majority of the listed clients in one field from Darjan's list? Only three are: Team Vision (Hawaii homes and residential communities), Rev Pop (Milwaukee restaurants and bars, its largest category) and Scribe (6 of 11 featured projects are restaurants and food). They now carry an industry line. The rest have mixed portfolios (for example Life Web & Design 5 of 12 construction, Kris Chislett about 16 of 60 construction), so they stay project.

## 2026-10-07, no opening line instead of a weak one
- Darjan found the "project" lines (praise of one site) the weakest, and they were 70 of 101. Josh Braun's split: with a real trigger, open with it; without one, do not invent personalization but ask about the problem. Version A already does that, so a weak line now gives way to none.
- New angle `none`: no opening line on purpose. The app sends version A without its opening paragraph, or version C with one fixed first line from Settings ("I had a few ideas on how {agency} could take on more website work without hiring for it.", after Eric Nowoslawski's "I had some ideas" opener). Never B. Such a lead still waits for Darjan's Ready on Opening lines.
- Order of angles to look for: hiring, award (30 days), owner, industry (a project from a field Darjan has designed for, the only way "project" stays), else none.
- Version A's question is now "When a few website projects land at {agency} at the same time, does the design side keep up, or is that where things start to slip?" (the deadline-or-weekend question was too heavy as a first line).

## 2026-10-07, nine email versions, chosen by angle
Darjan and Claude rewrote the first emails. The angle now decides the email in the outreach app: nine versions (A1, A2, B1, B2, C1, C2, D, E, F) for seven angles. Award and none have two versions each, one picked at random per lead; each version has its own subject except A2, whose subject Darjan writes per lead, and the versions from the sections above (A or C for owner, "Work like that" in B) no longer apply.

| Angle | Email | Subject | Opening line |
|---|---|---|---|
| `hiring` | D | your designer opening | the open designer job, posted in the last 50 days |
| `valley` | F | Fresno connection | none, the email names the town |
| `award` | B1 or B2 (random, fixed per lead) | after the win / busy after the win? | the award |
| `owner` | A1 | your take | what the owner said or wrote |
| `hobby` | A2 | written by Darjan per lead | written by Darjan in the app; the researcher gives only the source link |
| `industry` | E | your clients | written by the tool |
| `none` (and old `project` lines) | C1 or C2 (random, fixed per lead) | without hiring / busy stretches | none |

- Which angle a lead gets when it fits more than one: hiring first, then hobby (a found hobby is never traded for another angle, Darjan, 7 Oct 2026), then valley, owner, award, industry, none. Owner comes before award because, with awards from the whole year, an award no longer goes stale in days, and what the owner thinks is the stronger premise.
- The app sends ready leads in the same order. Darjan does not mind the order beyond that only Ready leads go out; hiring goes first because a job opening closes.
- A project line on its own is no longer used. An open designer job counts when it was posted in the last 50 days and is still open (Darjan, 7 Oct 2026; the 30 days in the sections above no longer apply).
- **The opening line is only the premise, 1 to 3 sentences, with no reaction or question at the end.** Every email now follows it with a fixed sentence that does the bridging, so a line that already ends in a reaction or question gives two in a row. Owner (A1) is followed by "It's clear you care how the work turns out, and that's usually what makes outside help hard to say yes to.", so the owner line must be about how they run the business (clients, quality, process, design, team). Private things (family, how the agency was founded) do not fit; such a lead gets `none`. A hobby or team from Darjan's list (see `hobby` below) is not an owner line either, it gets `hobby`. Award (B1, B2) is followed by "A win like that..." or "Wins like that...", so the line just states the award, in the form "Saw {agency} took [award] for [project] in [month]." An award from the current year is enough (Darjan, 7 Oct 2026), not only the last 30 days.
- **`valley`**: Darjan worked four years for an agency in Fresno. Every agency in California's Central Valley (Wikipedia's 18 counties) gets F unless it is hiring or a hobby was found. So for these agencies the researcher looks only for an open designer job and a hobby, nothing else. The tool sets this itself from the city (`store.apply_valley`, run by `openings` and `restatus`); the town list is `store.CENTRAL_VALLEY`. No opening line is needed, one already written stays in leads.csv but is not sent.
- **`industry`** only when the agency says on its own site that it builds websites for one or two industries from Darjan's list (the portfolio need not show it). The researcher gives the tool that sentence as `industry_text` with the page as `opening_source_url`, and the tool writes "Noticed {agency} focuses on websites for dental practices." (`leadtool/industry.py`, which also knows other names for each industry, such as lawyer or attorney for law firms). Narrowest first: one or two industries, then "home service businesses" (said outright, or three or more home-service industries), then "small businesses" only when that is the site's main message. Three or more mixed industries is not a specialist: no E. Try a text with `python -m leadtool industry "..."`.
- Industry list, after Darjan dropped schools, cafes, cocktail bars and gardening: construction, renovation, dentists, clinics, auto detailing, lawyers, vets, doctors, healthcare, heavy machinery, finance, landscaping, real estate, housing, education centers, plumbers, HVAC, restoration, farms, internet providers, fitness centers, commercial and residential solar, lighting, accounting, pest control, restaurants, insurance.
- **`hobby` (A2)**: a hobby or team Darjan and the owner share. Darjan follows woodworking, basketball, soccer, cycling, Arsenal FC, Miami Heat, the Pittsburgh Steelers and old cars (80s cars, classics). He writes the opening line and the subject for these leads himself, in the outreach app (Opening lines, or the lead's page), not in the sheet; Batch new leads never replaces them once written. The email continues with "That's my world too, so it couldn't wait.", so the line has to name the interest itself (a fan of, into, restores), not one event. The research session does not write hobby lines: when it finds a public mention of one of these interests, it sets angle `hobby` with only the source link in `opening_source_url` (no line), and the lead is not given any other angle, unless it is hiring a designer. The lead then shows on Opening lines under "No opening line yet" with that link, for Darjan to write.

## 2026-10-07, every lead reworked for the nine email versions
- All 130 leads with the owner's own address were reworked against the angle order above (hiring, hobby, valley, owner, award, industry, none). The file is `openings/rework_2026-10-07.json`. Result: 98 none, 12 owner, 8 industry, 5 hobby, 4 valley, 3 award, 0 hiring. No project lines remain.
- Hiring: no open designer job with a date in the last 50 days. Perspektiiv's careers page was last modified 28 Apr 2026 and The Creative Momentum's Senior Designer page 15 Jul 2020 (their sitemaps), so neither counts.
- Hobby: found on the agencies' own team and about pages (Circle City Digital, Bless Web Designs, RedX, Pear Analytics, ShiftWeb). Only the source link is stored; Darjan writes the line.
- Owner lines are premise only, about how the owner thinks about the work, from their signed posts on the agency site or their own blog, at most 12 months old. Founding stories (Muletown, BDX, Leanne Digital, Proof, Startup Production) no longer count, so those leads moved to none or industry.
- Award lines state the award only, from a 2026 listing whose year is on the page (Chariot, Red Spot, Big Red Jelly). YEG Digital and Perspektiiv also have 2026 awards but keep owner, which comes first.
- Industry lines come from the tool, fed with the agency's own sentence. "Small businesses" was used only where that is the site's headline or first line (Mvestor, dandelion, Black Door, Branch, Daor).
- kcwebdesigner.com was left out on purpose: the listed owner died in 2025, so the lead stays not ready.

## 2026-10-07, review of the reworked lines (Darjan and Claude)
- Owner lines no longer all open with "In your post ... you wrote". Each is phrased its own way (the idea first and the source after, or the source without "you wrote"), with the same verified content. Keep that variety in new lines.
- Four owner lines got a better quote from the same source: 1Brand (rankings drop when the technical side gets less care than the visual side, not because of good design), Southern Digital (shorter), Marvel (generic sites are basically free now, so real experience gets more valuable), Bonfire (the firms that get the call make it easy to see their experience fits).
- Moved to none: Exalto (no author on the page, reads as SEO copy), Big Red Jelly (the "50Pros 2026 Top 10 Agency" is a badge among many Clutch badges, not an award), and the five "small businesses" industry lines (Mvestor, dandelion, Black Door, Daor, and Branch, whose "small business focus" describes the agency itself, not its clients). "Small businesses" is too broad for E to mean anything.
- Awards checked: Chariot (Webby People's Voice 2026, on the Webby site) and Red Spot (#1 Dallas web design company on Clutch, 2026, on their awards page) stay.
- Result, 130 ready leads: 105 none, 11 owner, 5 hobby, 4 valley, 3 industry, 2 award. File `openings/review_2026-10-07.json`.

## 2026-10-08, four more owner lines to none; Ready only where a line is sent
- Darjan did not like Just By Design (code, while Darjan does design only), Lake Design (a side note from a portfolio write-up), Southern Digital (SEO, and published August 2025) and Bonfire (long, about her clients' marketing). All four moved to none. Owner is now 7: Thrive, Idaho Websites, Perspektiiv, Launch Kit, YEG Digital, 1Brand, Marvel Marketing.
- In the outreach app only a line that goes into the email waits for Darjan's Ready: hiring (D), owner (A1), award (B1, B2) and industry (E). A hobby line (A2) counts as approved when Darjan saves it. Leads that get C1, C2 or F show no line and go out without a Ready.
- kcwebdesigner.com is skipped (listed owner died in 2025), and Darjan's two quincylou.com test rows were removed from the sheet and the app.
