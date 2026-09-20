# CRO Page Audit Tool

A one-person lead magnet. Paste a URL, the app fetches that page, scores it against a
conversion-rate-optimization rubric with the Claude API, and saves the report behind a permanent
link you can send to a prospect.

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

The CTA banner is skipped entirely if either CTA value is missing.

## Routes

| Route | Access | What it does |
| --- | --- | --- |
| `/` | Password | Sign in, submit a URL, redirect to the new report |
| `/dashboard` | Password | Past audits, newest first, with a copyable report link |
| `/report/[id]` | Public | The saved report. Reads the database only, never calls the API |
| `/api/audit` | Session cookie | `POST { url, forceRerun? }`. Returns 401 without a session |
| `/api/login`, `/api/logout` | Public | Sets and clears the signed session cookie |

## How a run works

1. The URL is normalized (scheme added, tracking params stripped, private and non-http hosts
   rejected). That normalized string is what gets stored and matched on.
2. If an audit for the same normalized URL exists from the last 7 days and `forceRerun` is not
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
- One shared password, not real multi-user auth. The session is a signed, HTTP-only cookie that
  expires after 12 hours.

## Scripts

```bash
npm run dev        # development server
npm run build      # prisma generate + next build
npm run start      # production server
npm run typecheck  # tsc --noEmit
```
