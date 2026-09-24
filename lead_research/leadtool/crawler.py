"""Direct site crawler: robots.txt aware, collects emails and service signals.

Used by `python -m leadtool crawl <domain>` (one site) and by
`python -m leadtool recheck` (every qualified row).
"""
import re
import time
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; evie-lead-research/1.0; +https://evie.design)"
PAGES = ["", "contact", "contact-us", "about", "about-us", "team", "our-team",
         "privacy-policy", "privacy", "terms", "careers"]
LINK_HINTS = ("contact", "about", "team", "who-we-are", "our-story", "people", "privacy", "careers")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
WEB_SERVICE_RE = re.compile(r"web(site)?\s*(design|redesign)|website development|web development", re.I)
NOT_EMAIL_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".js", ".css")
MAX_PAGES = 14


def _robots(base):
    rp = robotparser.RobotFileParser()
    try:
        r = requests.get(urljoin(base, "/robots.txt"), headers={"User-Agent": UA}, timeout=15)
        rp.parse(r.text.splitlines() if r.status_code == 200 else [])
    except requests.RequestException:
        rp.parse([])
    return rp


def _cf_decode(hexstr):
    """Cloudflare email protection: first byte is the XOR key."""
    try:
        key = int(hexstr[:2], 16)
        return "".join(chr(int(hexstr[i:i + 2], 16) ^ key) for i in range(2, len(hexstr), 2))
    except ValueError:
        return ""


def _emails_from(soup, html):
    found = set()
    for a in soup.select('a[href^="mailto:"]'):
        found.add(a["href"][7:].split("?")[0].strip())
    for el in soup.select("[data-cfemail]"):
        found.add(_cf_decode(el["data-cfemail"]))
    for m in re.findall(r"/cdn-cgi/l/email-protection#([0-9a-fA-F]+)", html):
        found.add(_cf_decode(m))
    found.update(EMAIL_RE.findall(soup.get_text(" ")))
    return {e.lower().strip(".") for e in found
            if "@" in e and not e.lower().endswith(NOT_EMAIL_SUFFIX)}


def crawl(domain, delay=0.5):
    base = f"https://{domain}/"
    rp = _robots(base)
    found = {"emails": {}, "services_url": "", "offers_websites": False, "pages": [], "error": ""}
    queue = [urljoin(base, p) for p in PAGES]
    seen = set()
    while queue and len(found["pages"]) < MAX_PAGES:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        if not rp.can_fetch(UA, url):
            continue
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        except requests.RequestException as e:
            found["error"] = type(e).__name__
            continue
        if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
            continue
        host = (urlparse(r.url).hostname or "").removeprefix("www.")
        if host and host != domain and not host.endswith("." + domain):
            continue  # redirected off-site
        if r.url in found["pages"]:
            continue  # several paths redirected to the same page
        found["pages"].append(r.url)
        soup = BeautifulSoup(r.text, "html.parser")
        for addr in _emails_from(soup, r.text):
            found["emails"].setdefault(addr, r.url)
        if WEB_SERVICE_RE.search(soup.get_text(" ")):
            found["offers_websites"] = True
            if "service" in urlparse(r.url).path and not found["services_url"]:
                found["services_url"] = r.url
        if url == base:  # follow the site's own About/Team/Contact links
            for a in soup.select("a[href]"):
                href = urljoin(base, a["href"]).split("#")[0]
                if urlparse(href).hostname in (domain, "www." + domain) and \
                        any(h in href.lower() for h in LINK_HINTS):
                    queue.append(href)
        time.sleep(delay)
    return found
