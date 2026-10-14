import sys,json
sys.path.insert(0,'/home/user/quincy-lou-cro/lead_research')
from concurrent.futures import ThreadPoolExecutor
from leadtool import icypeas
from leadtool.compose import guesses
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from mx import has_mx
STOP=[False]
OUT='/tmp/leadwork/guess_results.jsonl'
def run(line):
    name,domain=line.split("|")[:2]
    tried=[]
    if STOP[0]: return dict(name=name,domain=domain,error='stopped, Icypeas unavailable',tried=tried)
    if has_mx(domain) is False: return dict(name=name,domain=domain,email=None,tried=[],note='no MX, no credit spent')
    for c in guesses(name,domain):
        try: ok=icypeas.verify(c)
        except icypeas.IcypeasUnavailable as e:
            # An error is not a rejection: the guesses are not tried, so the agency must not be recorded as skipped.
            STOP[0]=True
            return dict(name=name,domain=domain,error=str(e),tried=tried)
        tried.append(c)
        if ok: return dict(name=name,domain=domain,email=c,tried=tried)
    return dict(name=name,domain=domain,email=None,tried=tried)
from leadtool import store
known=store.known_domains()
lines=[l.strip() for l in open(sys.argv[1]) if l.strip() and l.split('|')[1].strip() not in known]
print('skipping known:',[l for l in open(sys.argv[1]) if l.strip() and l.split('|')[1].strip() in known])
with ThreadPoolExecutor(4) as ex:
    for r in ex.map(run,lines):
        open(OUT,"a").write(json.dumps(r)+"\n"); print(r["domain"],r.get("email"),len(r["tried"]),r.get("error",""),flush=True)
print("credits",icypeas.credits_used())
