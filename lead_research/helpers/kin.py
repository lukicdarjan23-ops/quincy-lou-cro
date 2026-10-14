import requests,re,json
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
UA="Mozilla/5.0 (compatible; evie-lead-research/1.0; +https://evie.design)"
t=requests.get("https://kinsta.com/agency-directory/",headers={"User-Agent":UA},timeout=40).text
slugs=sorted(set(re.findall(r"kinsta\.com/agency-directory/([a-z0-9\-]+)/",t)))
def f(sl):
    try: h=requests.get(f"https://kinsta.com/agency-directory/{sl}/",headers={"User-Agent":UA},timeout=30).text
    except Exception: return None
    s=BeautifulSoup(h,"html.parser")
    for x in s(["script","style","nav","header","footer"]): x.decompose()
    tx=re.sub(r"\s+"," ",s.get_text(" ",strip=True))
    m=re.search(r"Match me with this agency ([\d,\$\+\- ]+|Under[^A-Z]*|Over[^A-Z]*)?\s*(United States|Canada|[A-Z][a-z]+(?: [A-Z][a-z]+)*)\s+((?:https?://)?(?:www\.)?[a-z0-9\-\.]+\.[a-z]{2,})",tx)
    return dict(slug=sl,country=m.group(2) if m else "",site=m.group(3) if m else "",text=tx[:500])
with ThreadPoolExecutor(8) as ex: res=[r for r in ex.map(f,slugs) if r]
json.dump(res,open(f"{__import__('os').path.dirname(__file__)}/kin.json","w"))
print(len(res),sum(1 for r in res if r['country'] in('United States','Canada')))
