import sys,re,requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
UA="Mozilla/5.0 (compatible; evie-lead-research/1.0; +https://evie.design)"
def get(u):
    try:
        r=requests.get(u,headers={"User-Agent":UA},timeout=20)
        return r if r.status_code==200 else None
    except Exception: return None
for d in sys.argv[1:]:
    r=get(f"https://{d}/") or get(f"https://www.{d}/")
    if not r: print("##",d,"FAIL"); continue
    s=BeautifulSoup(r.text,"html.parser")
    md=s.find("meta",attrs={"name":"description"})
    desc=(md["content"][:160] if md and md.get("content") else "")
    links=[urljoin(r.url,a["href"]).split("#")[0] for a in s.select("a[href]")]
    team=[l for l in links if re.search(r"/(about|team|our-team|meet|people|who-we-are|leadership)[^/]*/?$",l,re.I) and d in l]
    cnt="";snip=""
    if team:
        rr=get(team[0])
        if rr:
            t=BeautifulSoup(rr.text,"html.parser")
            for x in t(["script","style","nav","footer","header"]): x.decompose()
            heads=[h.get_text(" ",strip=True) for h in t.select("h2,h3,h4,h5")]
            tx=re.sub(r"\s+"," ",t.get_text(" ",strip=True))
            cnt=f"{len(heads)} heads, {len(re.findall(r'(Designer|Developer|Manager|Director|Strategist|Specialist|Producer|Coordinator|Writer|Engineer|Founder|Owner|Principal|President|Partner)',tx))} roles"
            snip=tx[:260]
            tm=team[0]
    print(f"## {d} | {desc[:110]} | CITY {list(dict.fromkeys(__import__('re').findall(r'([A-Z][a-z]+(?: [A-Z][a-z]+)?),? ((?:AL|AZ|AR|CA|CO|CT|DC|DE|FL|GA|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|ON|BC|AB|QC|NS|NB|SK|MB))[ ,]+\d?', __import__('re').sub(r"\s+"," ",BeautifulSoup(r.text,"html.parser").get_text(" ",strip=True)))))[:3]}")
    print(f"## {d} | {desc}\n   {team[0] if team else 'no team link'} | {cnt}\n   {snip}")
