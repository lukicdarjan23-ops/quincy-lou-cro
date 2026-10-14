import sys,re,os,ast
sys.path.insert(0,'/home/user/quincy-lou-cro/lead_research')
from leadtool.compose import ascii_slug
doms=open(sys.argv[1]).read().split()
NAMEPAIR=re.compile(r"([A-Z][a-z]+)(?:\s[A-Z]\.)?\s([A-Z][a-zA-Z'\-]+)")
for d in doms:
    f=f"out/{d}.txt"
    if not os.path.exists(f): continue
    t=open(f).read().splitlines()
    pe=[l for l in t if l.startswith(" personal")]
    if not pe: continue
    try: emails=ast.literal_eval(pe[0].split(": ",1)[1])
    except Exception: continue
    if not emails: continue
    segs=[l for l in t if l.startswith("  OWN")]
    hits=[]
    for e,src in emails.items():
        loc=e.split("@")[0].lower().replace("%20","")
        for s in segs:
            for m in NAMEPAIR.finditer(s):
                fn,ln=ascii_slug(m.group(1)),ascii_slug(m.group(2))
                if not fn or not ln: continue
                if loc in {fn,fn+ln,fn[0]+ln,fn+"."+ln,fn+ln[0],ln} :
                    hits.append((m.group(0),e,s.strip()[:130]))
    if hits: print(d,hits[0])
