# Research helpers (14 Oct 2026 session)

Small scripts used to speed up the lead research. They write scratch output to `/tmp/leadwork` (create it first). Run from the repo root unless noted.

| script | what it does |
|---|---|
| `wpe.py`, `kin.py` | pull agency profiles from the WP Engine and Kinsta partner directories (robots.txt allows it) and list US and Canada sites |
| `runtri.sh LIST` | runs `triage.py` on every domain in LIST that is not in leads.csv, output in `/tmp/leadwork/out/` |
| `triage.py DOMAIN` | robots-aware look at home, about, team, contact and careers pages: service pages, own-site personal emails, owner/role snippets, hobby, award, industry and job hits |
| `own.py LIST` | prints only domains where a personal address on the agency's own site matches a person named near a founder or owner role |
| `qual.py DOMAIN` | meta description, city, team page link and a head count, to judge size |
| `city.py`, `page.py N URL`, `lastmod.py URL KEY`, `recent.py DOMAIN` | city from address, page text, sitemap lastmod (job dates), posts of the last 12 months |
| `guess_names.py FILE` | FILE has `Full Name|domain` lines. Runs Icypeas guesses one at a time per agency (stops at the first sure address) and skips domains already in leads.csv. An `error` in the output means Icypeas was unavailable (for example out of credits), not that the guesses failed |
| `mk.py` | builds batch json (`B.A(...)`) and runs `add` and `openings none` (`finish`) |

`add` accepts two extra fields written for this flow. `icypeas_verified` is an address already confirmed in the session, so no second credit is spent. `guesses_tried` marks an agency whose guesses all failed, so `add` records it as `skip: no owner email` without guessing again.

## Cheap flow (added 14 Oct 2026)
1. Put candidate domains in a file, one per line.
2. `python helpers/pipeline.py LIST.txt` does every free check in order (known in leads.csv, site opens, web design page, not solo, not big, MX record, owner name, owner address on site) and prints one line per survivor. Survivors without an address on their site are written to `/tmp/leadwork/guess_queue.txt`.
3. Only those go to `python helpers/guess_names.py /tmp/leadwork/guess_queue.txt`. It checks MX again, tries only `first@` and `flast@`, and stops everything at the first `insufficient_credits` error.
4. Step 2 can be delegated to the `lead-screener` subagent (`.claude/agents/lead-screener.md`, model haiku), which only runs the script and returns the table. Tested on 5 domains, 9 seconds. The main session then decides and writes the batch.

`mx.py` checks MX over DNS-over-HTTPS because plain DNS is blocked in the sandbox.

## Further savings (added 14 Oct 2026, later)
- `screened.csv` (in `lead_research/`) remembers every domain the pipeline dropped and why, so it is never read twice. It was seeded with the 421 domains screened on 14 Oct. `--recheck` ignores it; `python helpers/pipeline.py --mark domain.com "reason"` records a domain you rejected by hand.
- `triage.py` also opens privacy, terms, legal and accessibility pages, blog author pages, and reads schema.org `"email"` from the page code, because owners sometimes put their own address there.
- When the site shows other staff addresses, `pipeline.py` reads the domain's pattern (first@, flast@, first.last@) and writes it as a third field in `guess_queue.txt`; `guess_names.py` then tries that single address (1 credit instead of 2).
- Owner names need evidence before they are queued for guessing: found on an about or team page, or next to "our founder", "I'm", "founded", "Meet <name>", or with the surname in the domain. Testimonial lines ("Mark Rogers, President Electra Sales") are rejected. Checked on 12 agencies from this session: 11 correct owners, 2 testimonial sites correctly empty.

## Models and effort (set once, 14 Oct 2026)
- `.claude/settings.json`: `model` claude-sonnet-5-5, `effortLevel` medium. Applies to every new session in this repository (the CRO app work too). `/model` or `/effort` in a session still override it for that session.
- `.claude/agents/lead-screener.md`: haiku, effort low. Only runs `pipeline.py`.
- `.claude/agents/owner-line-writer.md`: Opus, effort high. Reads one source and returns an owner line or NO LINE. Tested on Glantz ("brand your business to sell for more", 21 May 2026): the first prompt accepted it, the tightened prompt correctly returned NO LINE because the post is advice to readers, not how Glantz works. One call used about 58 thousand subagent tokens, so call it only for leads that already have a confirmed owner address and a promising source.
