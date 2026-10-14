"""Domain list in, short table out. Does every free check so Claude (and Icypeas) only see what can still qualify.

  python helpers/pipeline.py LIST.txt            LIST has one domain per line
Writes /tmp/leadwork/pipeline.json (all facts) and /tmp/leadwork/guess_queue.txt ("Full Name|domain" for guess_names.py).
Order, cheapest first, and a domain is dropped at the first failure:
  known in leads.csv -> site opens -> sells web design -> not solo -> not big -> MX exists -> owner name -> owner address on site
Only the survivors are printed, one line each. Dropped domains are printed as one summary line per reason.
Every dropped domain is appended to lead_research/screened.csv with its reason, and later runs skip it, so nobody
reads it twice. --recheck ignores screened.csv. To record a survivor you rejected by hand:
  python helpers/pipeline.py --mark domain.com "reason"
When the site shows other staff addresses, the domain's address pattern (first@, flast@, first.last@) is written as a
third field in guess_queue.txt, so guess_names.py tries one address instead of two.
"""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from leadtool import store
from leadtool.compose import ascii_slug
from leadtool.crawler import UA
from mx import has_mx
import csv, datetime

SCREENED = os.path.join(os.path.dirname(HERE), "screened.csv")


def load_screened():
    try:
        return {r["domain"]: r["reason"] for r in csv.DictReader(open(SCREENED))}
    except FileNotFoundError:
        return {}


def mark(rows):
    """Record dropped domains. One row per domain; a newer reason replaces the older one."""
    data = {}
    if os.path.exists(SCREENED):
        data = {r["domain"]: r for r in csv.DictReader(open(SCREENED))}
    today = datetime.date.today().isoformat()
    for d, why in rows: data[d] = {"domain": d, "reason": why, "date": today}
    with open(SCREENED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["domain", "reason", "date"])
        w.writeheader()
        for d in sorted(data): w.writerow(data[d])


def domain_pattern(emails, near, names):
    """first / flast / first.last / ... from other personal addresses on the site, or None when unsure."""
    found = []
    for e in emails:
        loc = e.split("@")[0].lower().replace("%20", "")
        for n in near.get(e, []) + names:
            parts = [ascii_slug(x) for x in n.split()]
            if len(parts) < 2 or not parts[0] or not parts[-1]: continue
            f, l = parts[0], parts[-1]
            kind = {f: "first", f[0] + l: "flast", f"{f}.{l}": "first.last", f + l: "firstlast", f"{f[0]}.{l}": "f.last"}.get(loc)
            if kind: found.append(kind); break
    if found:
        return max(set(found), key=found.count)
    locs = [e.split("@")[0].lower() for e in emails]
    if len(locs) >= 2 and all(re.fullmatch(r"[a-z]{3,9}", x) for x in locs): return "first"
    if len(locs) >= 2 and all(re.fullmatch(r"[a-z]+\.[a-z]+", x) for x in locs): return "first.last"
    return None

W = "/tmp/leadwork"; OUT = f"{W}/out"; os.makedirs(OUT, exist_ok=True)
SOLO = re.compile(r"\b(one[- ]person|solo|freelanc\w+|one[- ]man|I'?m a (web )?designer|sole proprietor)\b", re.I)
TEAMLINK = re.compile(r"/(about|team|our-team|meet|people|who-we-are|leadership|our-story)[^/]*/?$", re.I)
ROLE = r"(?i:(?:co-?)?(?:founder|owner|ceo|president|principal|managing partner|partner))"
NAME = r"([A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-zA-Z'\-]+)"
BAD = re.compile(r"[“”\"]|testimonial|review|\bof [A-Z]|\bat [A-Z]|Owner,|CEO,|Founder,", re.I)


def triage(d):
    f = f"{OUT}/{d}.txt"
    if not os.path.exists(f):
        with open(f, "w") as fh:
            subprocess.run([sys.executable, f"{HERE}/triage.py", d], stdout=fh, stderr=subprocess.STDOUT, timeout=150)
    return open(f).read().splitlines()


def size_and_city(d):
    """(solo?, head count, city) from the team/about page and the home page."""
    heads, solo, city = 0, False, ""
    try:
        r = requests.get(f"https://{d}/", headers={"User-Agent": UA}, timeout=20)
        if r.status_code != 200:
            r = requests.get(f"https://www.{d}/", headers={"User-Agent": UA}, timeout=20)
        s = BeautifulSoup(r.text, "html.parser")
        txt = re.sub(r"\s+", " ", s.get_text(" ", strip=True))
        m = re.findall(r"([A-Z][a-z]+(?: [A-Z][a-z]+)?),? ((?:AL|AZ|AR|CA|CO|CT|DC|DE|FL|GA|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|ON|BC|AB|QC|NS|NB|SK|MB))[ ,]+\d?", txt)
        STOP = {"Ave", "Avenue", "Street", "St", "Road", "Rd", "Suite", "Blvd", "Company", "Review", "Full", "Plaza", "Drive", "Dr", "Way", "Lane", "Ln", "Ter", "Floor", "Markets", "Pros", "Design"}
        good = [(" ".join(w for w in c.split() if w not in STOP), st) for c, st in m]
        good = [g for g in good if g[0]]
        city = f"{good[0][0]}, {good[0][1]}" if good else ""
        team = [urljoin(r.url, a["href"]).split("#")[0] for a in s.select("a[href]")]
        team = [t for t in team if TEAMLINK.search(t) and d in t]
        if team:
            rr = requests.get(team[0], headers={"User-Agent": UA}, timeout=20)
            t = BeautifulSoup(rr.text, "html.parser")
            for x in t(["script", "style", "nav", "footer", "header"]): x.decompose()
            ttxt = re.sub(r"\s+", " ", t.get_text(" ", strip=True))
            heads = len(t.select("h2,h3,h4,h5"))
            solo = bool(SOLO.search(ttxt[:1500])) and heads < 8
    except Exception:
        pass
    return solo, heads, city


def owner_of(lines, domain=""):
    """Best owner candidate, or None. Testimonials ("Mark Rogers, President Electra Sales") are the usual false hit,
    so a name only counts with enough evidence: found on an about/team page, or next to "our founder", "I'm",
    "founded", or with the surname in the domain. Names from news, blog or portfolio pages lose points."""
    import ast
    bad_first = {"Meet", "Call", "Email", "Contact", "Our", "Founder", "Owner", "President", "Hi", "About", "Team", "Learn", "More", "West", "East", "North", "South", "Full", "Read", "View", "Get", "Free", "Company", "Business", "Marketing", "Digital", "Web", "Design", "Click", "Book", "Schedule", "Content", "Ecommerce", "Strategy", "Software", "Systems", "Development", "Developer", "Creative", "Senior", "Lead", "Account", "Project", "Manager", "Director", "Brand", "Paid", "Social", "Media", "Technology", "Operations", "Services", "Solutions", "Agency", "Studio", "Group", "Inc", "LLC", "Results", "Hello", "Welcome", "Thanks", "Thank"}
    dom = re.sub(r"[^a-z]", "", domain.split(".")[0].lower())
    best, best_score = None, 1
    for l in lines:
        if not l.startswith("  OWN"): continue
        try: url, seg = ast.literal_eval(l.strip()[4:].strip())
        except Exception: continue
        if re.search(r"[“”\"]", seg): continue
        cands = [(m.group(1), m.group(2), False) for m in re.finditer(NAME + r"[,\s]+(?:(?:is |was )?(?:the|our) )?(" + ROLE + r")\b(?!\s+(?:Developer|Designer|Engineer|Strategist|Consultant|Manager|Architect))", seg)]
        for m in re.finditer(r"\b" + ROLE, seg):  # role before the name; tried at every role so "Principal / Founder Paul Weinert" works
            mm = re.match(r"[\s:·|,/&+-]{1,4}" + NAME, seg[m.end():])
            if mm: cands.append((mm.group(1), m.group(0), True))
        for name, role, reverse in cands:
            w = name.split()
            if w[0] in bad_first or w[-1] in bad_first or (len(w[-1]) > 1 and w[-1].isupper()): continue
            score = 0
            path = re.sub(r"^https?://[^/]+", "", url)
            if re.search(r"about|team|leadership|people|who-we|our-story|founder|meet|staff", path, re.I): score += 3
            if re.search(r"news|blog|testimonial|review|case|portfolio|work|press|award", path, re.I): score -= 3
            if re.search(r"\b(our|the) (founder|owner)|\bI'?m |\bI am |founded|started", seg, re.I): score += 2
            if re.search(r"\bMeet " + re.escape(w[0]), seg): score += 1
            if dom and ascii_slug(w[-1]) and ascii_slug(w[-1]) in dom: score += 2
            if re.search(r"[\u2013\u2014-]\s*" + ROLE, seg): score -= 3   # "Name - Owner Company" testimonial style
            if reverse and not role.lower().endswith("founder") and score < 3: score -= 2  # "President Electra Sales" off the team page
            if re.search(r"(?i)founder|owner", role) or re.search(r"(?i)^.{0,25}?(founder|owner)", seg[seg.find(name) + len(name):] if name in seg else ""): score += 1
            if score > best_score: best, best_score = (name, role), score
    return best


def run(d):
    if d in KNOWN: return d, "known", None
    if d in SEEN: return d, "already screened", None
    lines = triage(d)
    if not lines or "HOME FAIL" in lines[0]: return d, "site does not open (or bot protection)", None
    svc = [l for l in lines if l.startswith(" svc:")]
    if not svc or svc[0].split("|")[0].strip() == "svc: []": return d, "no web design service page found", None
    solo, heads, city = size_and_city(d)
    if solo: return d, "looks solo (first person, one person)", None
    if heads > 40: return d, f"too big ({heads} headings on team page)", None
    mx = has_mx(d)
    if mx is False: return d, "domain has no MX record", None
    own = owner_of(lines, d)
    if not own: return d, "no owner name found on site", None
    pe = [l for l in lines if l.startswith(" personal")]
    emails = {}
    if pe:
        import ast
        try: emails = ast.literal_eval(pe[0].split(": ", 1)[1])
        except Exception: pass
    fn, ln = ascii_slug(own[0].split()[0]), ascii_slug(own[0].split()[-1])
    ok = {fn, fn + ln, fn[:1] + ln, fn + "." + ln, fn + ln[:1], ln}
    onsite = next((e for e in emails if e.split("@")[0].lower().replace("%20", "") in ok), "")
    near = {}
    nl = [l for l in lines if l.startswith(" near names")]
    if nl:
        import ast
        try: near = ast.literal_eval(nl[0].split(": ", 1)[1])
        except Exception: pass
    names = [m.group(0) for l in lines if l.startswith("  OWN") for m in re.finditer(NAME, l)]
    pattern = "" if onsite else (domain_pattern(emails, near, names) or "")
    flags = [l.strip()[:3] for l in lines if l.startswith(("  HOB", "  AWARD", "  JOB", "  IND"))]
    return d, "ok", dict(domain=d, owner=own[0], role=own[1], city=city, heads=heads, onsite=onsite, pattern=pattern,
                         svc=svc[0].split("[")[1].split("]")[0].split(",")[0].strip(" '"), flags=sorted(set(flags)))


if __name__ == "__main__":
    if sys.argv[1] == "--mark":
        mark([(sys.argv[2], sys.argv[3])]); print("marked", sys.argv[2]); sys.exit()
    recheck = "--recheck" in sys.argv
    sys.argv = [a for a in sys.argv if a != "--recheck"]
    KNOWN = store.known_domains()
    SEEN = {} if recheck else load_screened()
    doms = [x.strip() for x in open(sys.argv[1]).read().split() if x.strip()]
    with ThreadPoolExecutor(10) as ex: res = list(ex.map(run, doms))
    keep = [r[2] for r in res if r[1] == "ok"]
    drops = {}
    for d, why, _ in res:
        if why != "ok": drops.setdefault(why, []).append(d)
    json.dump(keep, open(f"{W}/pipeline.json", "w"), indent=1)
    with open(f"{W}/guess_queue.txt", "w") as q:
        for k in keep:
            if not k["onsite"]: q.write(f"{k['owner']}|{k['domain']}|{k['pattern']}\n")
    print(f"{len(doms)} domains, {len(keep)} survive")
    for k in keep:
        print(f"{k['domain']} | {k['city'] or '?'} | {k['owner']} ({k['role']}) | heads {k['heads']} | "
              f"{'ONSITE ' + k['onsite'] if k['onsite'] else 'needs guess' + (' (' + k['pattern'] + '@)' if k['pattern'] else '')} | {','.join(k['flags'])}")
    mark([(d, why) for why, ds in drops.items() if why not in ("known", "already screened") for d in ds])
    for why, ds in drops.items():
        print(f"dropped, {why}: {len(ds)}")
