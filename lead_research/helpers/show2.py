import sys,re,os
cands=open(sys.argv[1]).read().split()
N=r"([A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-zA-Z'\-]+)"
R=r"(?:Co-?)?(?:Founder|Owner|CEO|President|Principal|Managing Partner|Creative Director|Partner)"
for d in cands:
    f=f"out/{d}.txt"
    if not os.path.exists(f): continue
    t=open(f).read().splitlines()
    if not t or "HOME FAIL" in t[0]: continue
    svc=[l for l in t if l.startswith(" svc:")]
    if not svc or svc[0].split("|")[0].strip()=="svc: []": continue
    own=" ".join(l for l in t if l.startswith("  OWN"))
    names=[]
    for m in re.finditer(N+r"[,\s]+(?:\W\s)?("+R+r"[^.]{0,25})",own): names.append(m.group(1)+" ("+m.group(2)[:22]+")")
    for m in re.finditer(r"("+R+r")[^A-Za-z]{1,6}"+N,own): names.append(m.group(2)+" ("+m.group(1)+")")
    names=list(dict.fromkeys(names))[:2]
    pe=[l for l in t if l.startswith(" personal")][0]
    em=re.findall(r"'([^']+@[^']+)'",pe)[:2]
    ex=[l.strip()[:3]+l.strip()[3:60] for l in t if l.startswith(("  HOB","  AWARD","  JOB"))][:1]
    print(d,"|",names,em,ex)
