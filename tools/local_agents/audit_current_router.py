#!/usr/bin/env python3
"""Read-only Cloud9 native local-agent readiness audit. Never loads a model."""
import argparse,json,os,pathlib,urllib.request,time,socket
ap=argparse.ArgumentParser()
ap.add_argument("--catalog",default="/srv/lxc/ia-compute/data/cloud9-engine-runtime/model-catalog.json")
ap.add_argument("--selection",required=True)
ap.add_argument("--engine-root",default="/srv/lxc/ia-compute/data/cloud9-engine-runtime")
ap.add_argument("--endpoint",default="http://192.168.1.219:8090")
ap.add_argument("--guardian",default="192.168.1.200:19755")
ap.add_argument("--guardian-request-gib",type=float,default=4.0)
ap.add_argument("--output")
a=ap.parse_args()
sel=json.loads(pathlib.Path(a.selection).read_text())
cat=json.loads(pathlib.Path(a.catalog).read_text())
by={m["id"]:m for m in cat["models"]}
alias_owner={}
errors=[]
for m in cat["models"]:
 for alias in [m["id"],*m.get("aliases",[])]:
  s=alias.casefold()
  if s in alias_owner and alias_owner[s]!=m["id"]:
   errors.append(f"alias collision {alias}")
  alias_owner[s]=m["id"]
rows=[]
for x in sel["roles"]:
 m=by.get(x["model_id"])
 if m is None:
  errors.append("missing catalog role "+x["model_id"])
  continue
 backend=pathlib.Path(a.engine_root)/"current"/m["backend"]/"bin/llama-server"
 gguf=pathlib.Path(m["model"])
 draft_missing=[]
 for i,arg in enumerate(m.get("extra_args",[])):
  if arg=="--model-draft" and i+1<len(m["extra_args"]):
   if not pathlib.Path(m["extra_args"][i+1]).is_file():
    draft_missing.append(m["extra_args"][i+1])
 exists=gguf.is_file() and backend.is_file() and not draft_missing
 if not exists: errors.append("missing file in "+m["id"])
 rows.append({"role":x["role"],"model":m["id"],"uncensored":m.get("uncensored"),
              "gguf_exists":gguf.is_file(),"size_gib":round(gguf.stat().st_size/1073741824,3) if gguf.is_file() else None,
              "backend_binary_exists":backend.is_file(),"draft_files_missing":draft_missing,
              "catalog_tps_historical":m.get("benchmark",{}).get("decode_tps"),
              "gpu_mode":m.get("gpu_mode","exclusive"),"agent_quality_not_certified":True})
http={}
for path in ("/health","/v1/models"):
 try:
  with urllib.request.urlopen(a.endpoint+path,timeout=5) as f:
   payload=json.load(f)
  http[path]={"ok":True,"worker_model":payload.get("worker_model") if isinstance(payload,dict) else None,
              "model_count":len(payload["data"]) if isinstance(payload,dict) and "data" in payload else None}
 except Exception as e:
  http[path]={"ok":False,"error":str(e)};errors.append("router unreachable "+path)
actual=set()
if http.get("/v1/models",{}).get("ok"):
 try:
  with urllib.request.urlopen(a.endpoint+"/v1/models",timeout=5) as f:
   actual={m["id"] for m in json.load(f)["data"]}
 except Exception as e: errors.append("model API fetch failed "+str(e))
for x in rows:
 if x["model"] not in actual: errors.append("missing API model "+x["model"])
guardian={}
try:
 host,port=a.guardian.rsplit(":",1)
 with socket.create_connection((host,int(port)),timeout=4) as sk:
  sk.sendall(f"CHECK coexist-light {a.guardian_request_gib:.2f}\n".encode())
  data=sk.recv(16000).decode().strip()
  guardian=json.loads(data)
except Exception as e:guardian={"allow":None,"error":str(e)}
out={"date":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
     "catalog_mtime":time.strftime("%Y-%m-%d",time.gmtime(pathlib.Path(a.catalog).stat().st_mtime)),
     "selected_count":len(rows),"active_catalog_count":len(by),"selected_models":rows,
     "http":http,"gpu_guardian":guardian,"errors":errors,
     "routing_static_ready":not bool(errors),
     "gpu_execution_certified":False,
     "multi_agent_concurrency_certified":False,
     "production_ready_for_all_agents":False}
text=json.dumps(out,indent=2,ensure_ascii=False)
if a.output:pathlib.Path(a.output).write_text(text+"\n")
print(text)
raise SystemExit(0 if not errors else 2)
