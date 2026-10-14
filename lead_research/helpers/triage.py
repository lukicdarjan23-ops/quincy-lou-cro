import sys,re,time,json
sys.path.insert(0,'/home/user/quincy-lou-cro/lead_research')
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse
from leadtool.crawler import _robots,UA,_emails_from
from leadtool import store
GEN={"info","hello","contact","support","sales","team","office","admin","studio","ideas","help","marketing","careers","jobs","hi","mail","inquiries","web","design","seo","service","connect","start","work","billing","accounts","press","media","general","enquiries","projects","newbusiness"}
ROLE=re.compile(r"\b(founder|co-founder|owner|co-owner|ceo|president|principal|managing partner|creative director)\b",re.I)
NAME=re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-zA-Z'\-]+)\b")
HOB=re.compile(r"woodwork|basketball|soccer|cycling|cyclist|arsenal|miami heat|steelers|classic car|vintage car|old cars|muscle car|car restor|restor\w+ (a |my )?(\d{4}|classic|vintage)",re.I)
AW=re.compile(r"(webby|awwwards|addy|davey|w3 award|css design award|telly|muse award|communicator award|hermes)[^.]{0,80}",re.I)
IND=re.compile(r"(?:for|serving|specializ\w+ in|work with|clients include)\s[^.]{0,90}(dentist|dental|law firm|lawyer|attorney|contractor|construction|remodel|roofing|plumb|hvac|solar|real estate|landscap|restaurant|veterinar|clinic|medical|healthcare|insurance|accounting|fitness|pest|restoration|auto detail|farm)[^.]{0,60}",re.I)
JSONLD_EMAIL=re.compile(r'"email"\s*:\s*"(?:mailto:)?([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"')
JOB=re.compile(r"(web designer|ui designer|ui/ux designer|graphic designer|visual designer|product designer|senior designer|junior designer|creative designer)[^.]{0,60}",re.I)
def get(u,rp):
    if not rp.can_fetch(UA,u): return None
    try: r=requests.get(u,headers={"User-Agent":UA},timeout=20)
    except Exception: return None
    return r if r.status_code==200 and "html" in r.headers.get("content-type","") else None
def triage(d):
    d=d.removeprefix("www.")
    store_known=d in store.known_domains()
    base=f"https://{d}/"; rp=_robots(base)
    r=get(base,rp)
    if not r:
        r=get(f"https://www.{d}/",rp); base=f"https://www.{d}/"
    if not r: print(f"## {d}: HOME FAIL"); return
    host=urlparse(r.url).hostname.removeprefix("www.")
    soup=BeautifulSoup(r.text,"html.parser")
    title=(soup.title.string or "").strip()[:80] if soup.title else ""
    links={}
    for a in soup.select("a[href]"):
        h=urljoin(r.url,a["href"]).split("#")[0].rstrip("/")
        p=urlparse(h)
        if p.hostname and p.hostname.removeprefix("www.")==host: links[h]=a.get_text(" ",strip=True)
    svc=[h for h in links if re.search(r"web-?(site)?-?(design|develop)|website",h,re.I)][:2]
    pages=[h for h in links if re.search(r"about|team|people|who-we|our-story|leadership|staff|founder|meet|contact|career|jobs|award|news|blog$",h,re.I)][:9]
    # Owners often put their own address on pages nobody reads: privacy policy, terms, legal notice, blog author pages.
    extra=[h for h in links if re.search(r"privacy|terms|legal|imprint|disclaimer|accessibility|/author/",h,re.I) and h not in pages][:4]
    texts={r.url:r.text}; emails={}
    def grab(html,url):
        for e in _emails_from(BeautifulSoup(html,"html.parser"),html): emails.setdefault(e,url)
        for e in JSONLD_EMAIL.findall(html): emails.setdefault(e.lower(),url)  # schema.org "email" in page code
    grab(r.text,r.url)
    for p in pages+extra:
        time.sleep(.3); rr=get(p,rp)
        if not rr: continue
        texts[rr.url]=rr.text
        grab(rr.text,rr.url)
        if re.search(r"blog|news",p,re.I):  # follow up to two author pages from the blog index
            for a in BeautifulSoup(rr.text,"html.parser").select('a[href*="/author/"]')[:2]:
                au=urljoin(rr.url,a["href"]).split("#")[0]
                if au not in texts and urlparse(au).hostname and urlparse(au).hostname.removeprefix("www.")==host:
                    ra=get(au,rp)
                    if ra: texts[ra.url]=ra.text; grab(ra.text,ra.url)
    # Names printed next to each address, so the address pattern of the domain (first@, flast@) can be read off it.
    near={}
    for e,u in emails.items():
        plain=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",texts.get(u,"")))
        i=plain.lower().find(e)
        if i>=0: near[e]=list(dict.fromkeys(NAME.findall(plain[max(0,i-250):i+80])))[:4]
    owners=[];hob=[];aw=[];ind=[];job=[]
    for u,t in texts.items():
        s=BeautifulSoup(t,"html.parser")
        for x in s(["script","style","nav","footer","header"]): x.decompose()
        txt=re.sub(r"\s+"," ",s.get_text(" ",strip=True))
        for m in ROLE.finditer(txt):
            seg=txt[max(0,m.start()-45):m.end()+45]
            nm=NAME.findall(seg)
            if nm and len(owners)<5: owners.append((u.replace(base,"/"),seg))
        for m in HOB.finditer(txt):
            if len(hob)<2: hob.append((u.replace(base,"/"),txt[max(0,m.start()-60):m.end()+50]))
        for m in AW.finditer(txt):
            if "2026" in txt[m.start():m.end()+40] and len(aw)<2: aw.append((u.replace(base,"/"),txt[m.start():m.end()+40]))
        for m in IND.finditer(txt):
            if len(ind)<2: ind.append((u.replace(base,"/"),m.group(0)[:150]))
        if re.search(r"career|job",u,re.I):
            for m in JOB.finditer(txt):
                if len(job)<2: job.append((u,txt[m.start():m.end()+30]))
    own=[e for e in emails if e.split("@")[-1].removeprefix("www.").endswith(d) and e.split("@")[0] not in GEN]
    print(f"## {d} {'(KNOWN!)' if store_known else ''}| {title}")
    print(" svc:",svc[:2],"| pages:",len(texts))
    print(" personal emails:",{e:emails[e].replace(base,'/') for e in own})
    print(" near names:",{e:near.get(e,[]) for e in own})
    print(" generic:",[e for e in emails if e.split("@")[0] in GEN][:3])
    for o in owners[:4]: print("  OWN",o)
    for k,v in (("HOB",hob),("AWARD",aw),("IND",ind),("JOB",job)):
        for x in v: print(f"  {k}",x)
if __name__=="__main__":
    for d in sys.argv[1:]: triage(d)
