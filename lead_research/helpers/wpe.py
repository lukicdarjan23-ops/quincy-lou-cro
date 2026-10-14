import requests,re,json
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
UA="Mozilla/5.0 (compatible; evie-lead-research/1.0; +https://evie.design)"
t=requests.get("https://wpengine.com/agency-directory/",headers={"User-Agent":UA},timeout=30).text
slugs=sorted(set(re.findall(r"agency-directory\\?/([a-z0-9\-]+)",t)))
def f(sl):
    try:
        h=requests.get(f"https://wpengine.com/agency-directory/{sl}/",headers={"User-Agent":UA},timeout=30).text
    except Exception: return None
    s=BeautifulSoup(h,"html.parser")
    site=""
    for a in s.select('a[href^="http"]'):
        hh=a['href']
        if not re.search(r"wpengine|getflywheel|localwp|advancedcustom|nitropack|studiopress|deliciousbrains|torquemag|facebook|twitter|linkedin|instagram|youtube|google",hh): site=hh;break
    for x in s(["script","style","nav","header","footer"]): x.decompose()
    tx=re.sub(r"\s+"," ",s.get_text(" ",strip=True))
    m=re.search(r"MEMBER PARTNER|STRATEGIC PARTNER|PARTNER",tx)
    return dict(slug=sl,site=site,text=tx[:700],loc=(re.findall(r"([A-Z][A-Za-z\. ]+, [A-Z][A-Za-z ]+, (?:United States|Canada))",tx) or [""])[0])
with ThreadPoolExecutor(8) as ex: res=[r for r in ex.map(f,slugs) if r]
json.dump(res,open("/tmp/leadwork/wpe.json","w"))
print(len(res), sum(1 for r in res if r['loc']))
