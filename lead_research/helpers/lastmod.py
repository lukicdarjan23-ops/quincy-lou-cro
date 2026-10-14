import sys,re,requests
UA="Mozilla/5.0 (compatible; evie-lead-research/1.0; +https://evie.design)"
u=sys.argv[1]; host=re.match(r"https?://[^/]+",u).group(0)
def locs(url,depth=0):
    try: t=requests.get(url,headers={"User-Agent":UA},timeout=20).text
    except Exception: return []
    out=[]
    for m in re.finditer(r"<(?:url|sitemap)>(.*?)</(?:url|sitemap)>",t,re.S):
        b=m.group(1); l=re.search(r"<loc>([^<]+)</loc>",b); lm=re.search(r"<lastmod>([^<]+)</lastmod>",b)
        if l:
            if l.group(1).endswith(".xml") and depth<2: out+=locs(l.group(1),depth+1)
            else: out.append((l.group(1),lm.group(1) if lm else ""))
    return out
for sm in [host+"/sitemap_index.xml",host+"/sitemap.xml",host+"/wp-sitemap.xml"]:
    L=locs(sm)
    if L: break
key=sys.argv[2] if len(sys.argv)>2 else "career"
print(len(L),"urls")
for a,b in L:
    if re.search(key,a,re.I): print(b,a)
