import sys,re,requests,datetime as dt
UA="Mozilla/5.0 (compatible; evie-lead-research/1.0; +https://evie.design)"
cut=(dt.date(2026,10,14)-dt.timedelta(days=365)).isoformat()
def locs(url,depth=0):
    try: t=requests.get(url,headers={"User-Agent":UA},timeout=20).text
    except Exception: return []
    out=[]
    for m in re.finditer(r"<(?:url|sitemap)>(.*?)</(?:url|sitemap)>",t,re.S):
        b=m.group(1); l=re.search(r"<loc>([^<]+)</loc>",b); lm=re.search(r"<lastmod>([^<]+)</lastmod>",b)
        if l:
            if l.group(1).endswith(".xml") and depth<2: out+=locs(l.group(1),depth+1)
            else: out.append((l.group(1),lm.group(1)[:10] if lm else ""))
    return out
for d in sys.argv[1:]:
    host=f"https://{d}"
    L=[]
    for sm in ["/sitemap_index.xml","/sitemap.xml","/wp-sitemap.xml"]:
        L=locs(host+sm) or locs(f"https://www.{d}"+sm)
        if L: break
    posts=[(b,a) for a,b in L if b>=cut and re.search(r"/(blog|news|insights|articles|resources|journal|post)s?/[^/]+/?$|/20\d\d/",a)]
    posts.sort(reverse=True)
    print(f"## {d} {len(L)} urls, {len(posts)} recent posts")
    for b,a in posts[:5]: print("  ",b,a.replace(host,"").replace("https://www."+d,"")[:90])
