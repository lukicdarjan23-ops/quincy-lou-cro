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
