import sys,re,requests
from bs4 import BeautifulSoup
UA="Mozilla/5.0 (compatible; evie-lead-research/1.0; +https://evie.design)"
n=int(sys.argv[1])
for u in sys.argv[2:]:
    try:
        r=requests.get(u,headers={"User-Agent":UA},timeout=20)
        s=BeautifulSoup(r.text,"html.parser")
        for x in s(["script","style","nav","footer","header"]): x.decompose()
        t=re.sub(r"\s+"," ",s.get_text(" ",strip=True))
        print("##",u,r.status_code,len(t)); print(t[:n])
    except Exception as e: print("##",u,"ERR",type(e).__name__)
