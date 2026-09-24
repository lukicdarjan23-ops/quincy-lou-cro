"""Crawl every qualified agency site in parallel. Resumable: results are saved per site."""
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from leadtool import store
from leadtool.crawler import crawl

OUT = "crawl_results.json"
results = json.load(open(OUT)) if os.path.exists(OUT) else {}
lock = threading.Lock()
rows = [r for r in store.load_leads() if store.is_qualified(r) and r["domain"] not in results]


def job(domain):
    try:
        return domain, crawl(domain)
    except Exception as e:  # keep going, record the failure
        return domain, {"emails": {}, "pages": [], "error": repr(e)}


with ThreadPoolExecutor(12) as ex:
    for fut in as_completed([ex.submit(job, r["domain"]) for r in rows]):
        d, res = fut.result()
        with lock:
            results[d] = res
            json.dump(results, open(OUT, "w"), indent=1)
        print(f"{d}: {len(res['pages'])} pages, {len(res['emails'])} emails {res.get('error', '')}", flush=True)
ok = sum(1 for v in results.values() if v["pages"])
print(f"DONE crawled {len(results)} sites, {ok} reachable, "
      f"{sum(1 for v in results.values() if v['emails'])} with emails")
