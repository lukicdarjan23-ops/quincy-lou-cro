#!/bin/sh
# usage: runtri.sh listfile
S=/tmp/leadwork
cd /home/user/quincy-lou-cro
python - "$1" <<'P' > $S/todo.txt
import sys
known=set(open('/tmp/known.txt').read().split())
import os
S="/tmp/leadwork"
for d in open(sys.argv[1]).read().split():
    if d not in known and not os.path.exists(f"{S}/out/{d}.txt"): print(d)
P
cat $S/todo.txt | xargs -P 10 -I{} sh -c "timeout 100 python $S/triage.py {} > $S/out/{}.txt 2>&1"
