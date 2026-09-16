#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"sources.lock"
j=json.loads(p.read_text())
def head(url):
    out=subprocess.check_output(["git","ls-remote",url,"refs/heads/master"],text=True).strip()
    if not out: raise SystemExit(f"No master ref for {url}")
    return out.split()[0]
changed=[]
for key in ("upstream","atomic"):
    new=head(j[key]["repository"]); old=j[key]["commit"]
    if new!=old: j[key]["commit"]=new; changed.append((key,old,new))
if changed:
    from datetime import date
    j["tested_on"]=str(date.today())
    p.write_text(json.dumps(j,indent=2)+"\n")
    for k,o,n in changed: print(f"{k}: {o[:12]} -> {n[:12]}")
else: print("sources.lock already current")
