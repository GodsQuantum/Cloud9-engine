#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"sources.lock"
j=json.loads(p.read_text())
def head(entry):
    branch=entry.get("branch","master")
    ref=f"refs/heads/{branch}"
    out=subprocess.check_output(["git","ls-remote",entry["repository"],ref],text=True).strip()
    if not out: raise SystemExit(f"No {ref} for {entry['repository']}")
    return out.split()[0]
changed=[]
for key in ("upstream","atomic","prism"):
    if key not in j: continue
    new=head(j[key]); old=j[key]["commit"]
    if new!=old: j[key]["commit"]=new; changed.append((key,old,new))
if changed:
    from datetime import date
    j["observed_on"]=str(date.today())
    j.pop("tested_on",None)
    p.write_text(json.dumps(j,indent=2)+"\n")
    for k,o,n in changed: print(f"{k}: {o[:12]} -> {n[:12]}")
else: print("sources.lock already current")
