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
