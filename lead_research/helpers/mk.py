import json,sys
class B:
    def __init__(s,path): s.path=path; s.b=[]
    def A(s,name,site,city,team,svc,cn,title,csrc,verified=None,email=None,esrc=None,note="",country="USA",tried=False):
        d=dict(agency_name=name,website=site,country=country,city=city,team_size_estimate=team,why_fit=f"Sells website design. {svc}",contact_name=cn,contact_title=title,contact_source_url=csrc,research_note=note)
        if verified: d["icypeas_verified"]=verified; d["research_note"]=(note+"; " if note else "")+"owner address confirmed by Icypeas (14 Oct 2026)"
        if email: d.update(email=email,email_source_url=esrc,email_type="personal")
        if tried: d["guesses_tried"]=True; d["research_note"]=(note+"; " if note else "")+"Icypeas rejected the owner name guesses (14 Oct 2026)"
        s.b.append(d)
    def save(s): json.dump(s.b,open(s.path,"w"),indent=1); print(len(s.b),"records")
import subprocess,os
def finish(path,none_domains):
    os.chdir('/home/user/quincy-lou-cro/lead_research')
    out=subprocess.run(["python","-m","leadtool","add",path],capture_output=True,text=True).stdout
    print("\n".join(l for l in out.splitlines() if not l.startswith("  google") )[-600:])
    if none_domains:
        p=path.replace("batches/","openings/").replace(".json","_none.json")
        json.dump([{"domain":d,"angle":"none"} for d in none_domains],open(p,"w"))
        out=subprocess.run(["python","-m","leadtool","openings",p],capture_output=True,text=True).stdout
        print("\n".join(l for l in out.splitlines() if not l.startswith("  google"))[-600:])
