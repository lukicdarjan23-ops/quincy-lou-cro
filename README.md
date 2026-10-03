# CRO Page Audit Tool

A lead magnet with two sides.

- **Public analyzer** at `/`. A visitor answers three questions (page URL, the one action the
  page should drive, main traffic source), waits on a progress screen, then sees the overall score,
  the conversion killers found and a score plus diagnosis for each CONVERT factor. The fixes are
  not shown. They sit behind a "book a call" button and an email capture, and every email lands in
  the dashboard as a lead.
- **Owner dashboard** at `/dashboard`, behind one shared password. Run audits yourself, see leads
  and past audits, and copy the full report link to send to a prospect.

Report links are public but unguessable (UUID) and carry `noindex, nofollow`. Only people who
receive a link can see the report.

## Setup

```bash
cp .env.example .env     # then fill in the values
npm install
npx prisma migrate dev
npm run dev
```

`.env` holds every value. Prisma's CLI only reads `.env`, and Next.js reads `.env` plus
`.env.local`, so a single `.env` keeps both in sync. If you prefer to split them, put
`DATABASE_URL` in `.env` and the rest in `.env.local`.

| Variable | What it does |
| --- | --- |
| `DATABASE_URL` | SQLite file, e.g. `file:./dev.db` |
| `ANTHROPIC_API_KEY` | Key for the analysis call |
| `ANTHROPIC_MODEL` | Optional. Defaults to `claude-sonnet-5` |
| `AUDIT_TOOL_PASSWORD` | The single shared password for the owner pages |
| `QUINCY_LOU_CTA_TEXT` | Text of the CTA banner at the bottom of every report |
| `QUINCY_LOU_CTA_URL` | Where that banner links |
| `BOOKING_URL` | Optional. Where the public analyzer's booking buttons go. Falls back to `QUINCY_LOU_CTA_URL` |
| `PUBLIC_DAILY_LIMIT` | Optional. Public analyses per visitor IP per 24 hours. Defaults to 3 |

The CTA banner is skipped entirely if either CTA value is missing.

## Routes

| Route | Access | What it does |
| --- | --- | --- |
| `/` | Public | Landing page and the three-step analyzer |
| `/dashboard` | Password | Run an audit, leads, past audits, copyable report links |
| `/report/[id]` | Public | The full saved report. Reads the database only, never calls the API |
| `/api/analyze` | Public, rate limited | `POST { url, goal?, trafficSource? }`. Returns the score and findings, never the recommendations or the audit id |
| `/api/runs/[id]/lead` | Public | `POST { email, wantsMeeting }`. Saves a lead against a public run |
| `/api/audit` | Session cookie | `POST { url, forceRerun? }`. Returns 401 without a session |
| `/api/login`, `/api/logout` | Public | Sets and clears the signed session cookie |

## How a run works

1. The URL is normalized (scheme added, tracking params stripped, private and non-http hosts
   rejected). That normalized string is what gets stored and matched on.
2. If an audit for the same normalized URL, goal and traffic source exists from the last 7 days and `forceRerun` is not
   set, its ID comes straight back. No fetch, no API call.
3. Otherwise the page is fetched server-side: redirects followed, 15 second timeout, 3 MB cap,
   non-200 and non-HTML responses rejected with a readable error.
4. `src/lib/extract.ts` parses the HTML with cheerio into a fact sheet: headings, CTA-like
   elements and whether each label is generic or value-specific, phone number presence and
   whether it sits in the header or hero, testimonial blocks with name/title/photo/detail flags,
   likely-stock imagery, social proof numbers, trust badge mentions and whether they sit near a
   CTA, form fields, exit links, urgency language and whether it is backed by anything specific.
5. Pages with under 100 words of readable text stop here with an "insufficient content" error.
   Nothing is scored and nothing is saved.
6. The fact sheet plus a trimmed copy of the page text goes to Claude with the rubric
   (`src/lib/rubric.ts`) as the system prompt.
7. The response is validated against the schema in `src/lib/report-schema.ts`. Invalid JSON gets
   one corrective retry, then fails. A row is written only once a valid report exists, so a
   failed run never leaves a broken audit behind.

Deterministic values are recomputed rather than trusted: the overall score is the weighted
average of the seven CONVERT factors (Blockers weighted 1.5, Accelerators 1.0), status thresholds
come from the score (0-5.9 fix now, 6-7.9 improve, 8-10 solid), and factor order, names and types
are fixed.

## Public analyzer details

- Each public request writes a `PublicRun` row before anything is fetched, so failed runs count
  toward `PUBLIC_DAILY_LIMIT` too. Visitors are keyed by a salted hash of their IP, read from
  `x-forwarded-for`. Put the app behind a proxy that sets that header honestly.
- The browser gets the run id, never the audit id. The audit id opens `/report/[id]`, which
  includes the recommendations, so it stays in the dashboard.
- Goal and traffic source go into the prompt, so they are part of the 7 day reuse match.
- No email is sent yet. A lead is stored and the visitor is told the report is on its way, and the
  owner follows up from the dashboard. Wiring in a mail provider is a separate step.

## The rubric

- The Three Questions (Marty Greif) as the frame.
- The CONVERT framework (SiteTuners / Marty Greif): Clarity, Offer, Navigation, Validation,
  Emotion, Relevance, Traction, split into Accelerators and Blockers. Blockers are prioritized
  first, because they stop conversion outright while accelerators improve it at the margin.
- Greif's ranked trust signal hierarchy and Tim Ash's Four Pillars of Trust inside Validation.
- Tim Ash's Seven Deadly Sins of Landing Page Design as a secondary checklist.

Every score has to be grounded in something specific found on the page.

## Known limits, v1

- No headless browser. JavaScript-rendered single page apps can come back with little or no
  readable text, and those runs are rejected rather than guessed at. `src/lib/fetch-page.ts` is
  the only place that would change to swap in Playwright later.
- Visual hierarchy and real-versus-stock photos are inferred from HTML, file names, alt text and
  CSS classes, not from a rendered screenshot. The rubric tells Claude to say so wherever it is
  inferring.
- Message match is inferred without knowing the ad, email or search term that brought a visitor
  to the page.
- No PDF export. There is a small print stylesheet, nothing more.
- The public rate limit is per IP, so visitors behind one shared office IP share the limit, and
  someone rotating IPs can get around it.
- One shared password, not real multi-user auth. The session is a signed, HTTP-only cookie that
  expires after 12 hours.

## Scripts

```bash
npm run dev        # development server
npm run build      # prisma generate + next build
npm run start      # production server
npm run typecheck  # tsc --noEmit
```
