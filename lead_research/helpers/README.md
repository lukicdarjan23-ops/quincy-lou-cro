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
