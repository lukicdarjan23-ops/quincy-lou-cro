# Current rules (read this first)

Short version of what is in force as of 14 Oct 2026. `DECISIONS.md` is the full history with the reasons; open it only when a case is not covered here. When the two disagree, the newest section of DECISIONS.md wins, and this file should be updated.

## Who qualifies
- US or Canada, sells website design (a web design service page on its own domain), roughly 2 to 20 people. A two-person studio qualifies; a solo freelancer or an "I" site does not.
- Skip SEO or PPC only shops, pure dev shops, theme sellers, big agencies, and anyone selling white-label design to other agencies (competitors).
- Bot-protected sites (Cloudflare challenge, 403 to plain requests) are left alone. Respect robots.txt. No LinkedIn log-in or scraping.

## Order of work (stop at the first failure)
1. Not in `leads.csv` (`python -m leadtool known`) and not in `screened.csv`.
2. Qualifies (above).
3. Owner or founder by name, with a source URL.
4. Owner's own address. Either it is on the agency's own site, or Icypeas confirms a guess (`ultra_sure` or `sure`). info@, hello@, team@, contact@, studio@, an employee's address and data brokers (ZoomInfo, RocketReach and similar) do not count. A search query never contains the address being checked.
5. Only then the angle.

No owner address after the site and the guesses: add the agency anyway (`add` marks it `skip: no owner email`, it never reaches the sheet) and move on.

## Angle, take the first that fits
1. **hiring**: an open web, UI or visual designer job (the tool's check also accepts UX and graphic designer titles; no development or marketing in the title), posted in the last 50 days, still open. Give `job_title` and `posted_date` (job page or sitemap lastmod).
2. **hobby**: public mention that the owner is into woodworking, basketball, soccer, cycling, Arsenal FC, Miami Heat, the Pittsburgh Steelers or old cars. Give only the source link, no line; Darjan writes it. Beats everything except hiring.
3. **valley**: California's Central Valley. The tool sets it from the city; for these only check hiring and hobby.
4. **owner**: what the owner said or wrote about running the business (clients, quality, process, design, team), signed by the owner, at most 12 months old. Premise only, 1 to 3 sentences, no reaction, compliment or question. Phrase each line its own way. Not SEO, hosting or code topics, not private life or founding stories. Waits for Darjan's Ready.
5. **award**: a judged award from the current year (Webby, Awwwards, ADDY, Davey, Aster and similar). Give `award_name` and `award_evidence` copied exactly. Directory badges (Clutch, 50Pros, DesignRush, UpCity, The Manifest and similar) are not awards. Line form "Saw {agency} took [award] for [project] in [month]."
6. **industry**: the agency's own site names one or two industries from the list below as its clients. Give `industry_text` (that sentence) and its page; the tool writes the line. "Small businesses" or three or more mixed industries do not count.
7. **none**: nothing above fits. No line.

Industry list: construction, renovation, dentists, clinics, auto detailing, lawyers, vets, doctors, healthcare, heavy machinery, finance, landscaping, real estate, housing, education centers, plumbers, HVAC, restoration, farms, internet providers, fitness centers, commercial and residential solar, lighting, accounting, pest control, restaurants, insurance.

House style: no em dashes, no colons, no relative time ("last week"). Every fact has a source URL.

## Saving
- `python -m leadtool add batches/batchNN.json` (about 10 per batch), `python -m leadtool openings file.json` (REJECTED records failed a check), `python -m leadtool restatus`, `python -m leadtool sheet-sync`.
- Do not touch the outreach app. Darjan presses Batch new leads himself.
- New decisions go into DECISIONS.md; update this file if a rule changes.

## Cheap flow (saves Icypeas credits and Claude usage)
- Discovery without web search: `helpers/wpe.py`, `helpers/kin.py` (WP Engine and Kinsta partner directories). Web search with `blocked_domains` set to directories and listicles returns agencies' own sites. About 200 web searches per session.
- Screening: `python helpers/pipeline.py LIST.txt`, or the `lead-screener` subagent (haiku), which runs it and returns the table. Dropped domains go to `screened.csv` and are skipped next time.
- Guessing: `python helpers/guess_names.py /tmp/leadwork/guess_queue.txt`. Tries `first@` and `flast@` only, or the single address the domain's pattern points to, skips domains without MX, stops at the first `insufficient_credits`.
- Model and effort are set in `.claude/settings.json` (Sonnet 5.5, effort medium) and need no change. Screening goes to the `lead-screener` agent (haiku, effort low). Owner lines go to the `owner-line-writer` agent (Opus, effort high): give it agency, domain, owner and the source URL; it returns one openings record or NO LINE, and the main session saves it. Raise effort for one session with `/effort` only if a session keeps making judgment mistakes.
- Pending owner names waiting for credits: `pending_guesses.txt`; older leads to pick up: `candidates_backlog.csv`.

## Known exceptions
- kcwebdesigner.com: listed owner died in 2025, skipped.
- Icypeas ran out of credits on 14 Oct 2026 (510 used). Until credits are added, only addresses shown on the agency's own site can be used.
