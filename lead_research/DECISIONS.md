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
