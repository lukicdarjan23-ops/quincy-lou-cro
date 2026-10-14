import sys,re,requests
UA="Mozilla/5.0 (compatible; evie-lead-research/1.0; +https://evie.design)"
for d in sys.argv[1:]:
    found=[]
    for p in ["","contact","contact-us","about","about-us"]:
        try: t=requests.get(f"https://{d}/{p}",headers={"User-Agent":UA},timeout=15).text
        except Exception: continue
        t=re.sub(r"<[^>]+>"," ",t); t=re.sub(r"\s+"," ",t)
        found+=re.findall(r"([A-Z][A-Za-z\. ]{2,25}),?\s+([A-Z]{2})\s+(\d{5}|[A-Z]\d[A-Z])",t)
    from collections import Counter
    print(d,Counter(found).most_common(3))
