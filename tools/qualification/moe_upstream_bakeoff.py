#!/usr/bin/env python3
"""MoE upstream on-device benchmark; aborts BEFORE model load if coexistence is unsafe."""
from __future__ import annotations
import argparse,fcntl,hashlib,json,os,pathlib,socket,subprocess,threading,time,urllib.request,urllib.error
from pathlib import Path

MODELS={
 "pym":Path("/srv/lxc/ia-compute/data/models/qwen36-pym-q2-mtp/Qwen3.6-35B-A3B-Pym-Q2-MTP.gguf"),
 "flash_alternate":Path("/srv/lxc/ia-compute/data/models/strata/coder-iq1m/Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf"),
}
BINARIES={
 "upstream_b11840":Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/upstream-master36e-vulkan-gfx1103-20261023/bin/llama-server"),
 "upstream_b11844":Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/upstream-master062-vulkan-gfx1103-20261023/llama-server"),
}
GUARD=("192.168.1.200",19755)
LOCK=Path("/run/cloud9-gpu.lock")
URL="http://127.0.0.1:18139"
ROUTER="http://192.168.1.219:8090/health"
AUTOSUBS="http://192.168.1.219:8007/health"
LAB=Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/local-agent-readiness-20261024")
PROMPTS=[
 ("math","Calcule 25 × 37, puis explique en français différentes méthodes de vérification, étape par étape, avec exemples complémentaires."),
 ("code","Écris une fonction Python déterministe qui fusionne plusieurs itérateurs déjà triés et fournis des tests unitaires pour entrées vides, doublons et nombres négatifs."),
 ("fr","Explique en français comment une équipe peut diagnostiquer une panne intermittente sur un serveur, sans commander d'actions destructives, avec hypothèses et tests en lecture seule."),
]
def fetch(url,payload=None,timeout=4):
 body=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
 with urllib.request.urlopen(urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"} if body else {}),timeout=timeout) as r:
  return json.load(r)

def guardian(gib):
 with socket.create_connection(GUARD,timeout=4) as s:
  s.settimeout(4);s.sendall(f"CHECK coexist-light {gib:.2f}\n".encode());return json.loads(s.recv(16000))

def host_temp():
 best=[]
 for name in Path("/sys/class/hwmon").glob("hwmon*/name"):
  if name.read_text().strip() not in ("k10temp","amdgpu"):continue
  root=name.parent
  for p in root.glob("temp*_input"):
   try:best.append(float(p.read_text())/1000)
   except Exception:pass
 return max(best) if best else None

def psi_io_full():
 import re
 found=__import__("re").search(r"full avg10=([\d.]+)",Path("/proc/pressure/io").read_text())
 return float(found.group(1)) if found else None

def preflight(model_key,engine,mode):
 p=MODELS[model_key];b=BINARIES[engine]
 assert p.is_file() and b.is_file()
 if mode=="mtp2" and model_key!="pym":
  return {"admitted":False,"reasons":["DIFFERENT_FLASH_GSQ_MODEL_HAS_NO_PINNED_MTP_EVIDENCE"]}
 if model_key=="flash_alternate":
  # Strata GSQ-RCO IQ1_M is NOT the historical AD-4.27 + FR-Spec GGUF:
  # refusing a falsely matched benchmark, regardless of available RAM.
  shards=sorted(p.parent.glob("Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-*-of-00002.gguf"))
  assert len(shards)==2
  return {"admitted":False,"reasons":["FLASH_UNMATCHED_HISTORICAL_MODEL"],
          "actual_sharded_bytes":sum(x.stat().st_size for x in shards),
          "historical_17_878_tps_comparable":False,
          "note":"Separate GSQ-RCO/Strata quantization is not historical Flash-Next AD-4.27+FR-Spec"}
 gguf_gib=p.stat().st_size/(1024**3)
 # Reserve 21 GiB after paging the model in, plus 2 GiB native buffers.
 # These are conservative test admission budgets, NOT actual model residency.
 floor=round(gguf_gib+23.0,2)
 required_gtt=14.0  # Proven Pym ngl99 requirement from 2026-10-18 thermal audit
 g=guardian(required_gtt)
 io=psi_io_full()
 t=host_temp()
 why=[]
 if not g.get("allow"):why.append("OFFICIAL_GPU_GUARD_DENIED")
 if g.get("mem_available_gib",0)<floor:why.append("MODEL_SIZE_PLUS_PRODUCTION_RAM_RESERVE")
 if g.get("safe_total_gtt_gib",0)<required_gtt:why.append("INSUFFICIENT_GTT_FOR_MATCHED_FULL_OFFLOAD")
 if g.get("psi_memory_full_avg10",99)>=0.25:why.append("HOST_MEMORY_PSI")
 if io is None or io>=9:why.append("HOST_IO_PSI")
 if t is None or t>=76:why.append("TEMPERATURE_PREFLIGHT")
 if fetch(ROUTER,timeout=3).get("worker_model") is not None:why.append("ROUTER_WORKER_ACTIVE")
 try:
  autosubs=fetch(AUTOSUBS,timeout=3)
  if autosubs.get("status")!="ok" or autosubs.get("loaded_models")!=[]:why.append("AUTOSUBS_GPU_IN_USE_OR_HEALTH_UNKNOWN")
 except Exception:why.append("AUTOSUBS_GPU_HEALTH_UNREACHABLE")
 return {"admitted":not why,"reasons":why,"model_bytes":p.stat().st_size,"model_name":p.name,
         "binary_sha256":hashlib.sha256(b.read_bytes()).hexdigest(),
         "min_available_gib":floor,"required_gtt_gib":required_gtt,
         "guardian":{k:g.get(k) for k in ("allow","mem_available_gib","psi_memory_full_avg10","swap_used_percent","safe_total_gtt_gib","reasons")},
         "host_io_full_avg10":io,"max_host_gpu_temp_c":t,
         "note":"Flash GSQ-RCO is NOT the historical AD-4.27 + FR-Spec; invalid historical speed comparison"}

def stop_own(proc):
 if proc is None or proc.poll() is not None:return
 proc.terminate()
 try:proc.wait(timeout=4)
 except subprocess.TimeoutExpired:
  proc.kill();proc.wait(timeout=6)

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--engine",choices=sorted(BINARIES),required=True)
 ap.add_argument("--model",choices=sorted(MODELS),required=True)
 ap.add_argument("--mode",choices=["base","mtp2"],required=True)
 ap.add_argument("--run-id",required=True)
 ap.add_argument("--execute",action="store_true")
 a=ap.parse_args()
 if not(1<=len(a.run_id)<=45 and all(c.isalnum() or c in "-_" for c in a.run_id)):ap.error("invalid immutable run-id")
 report=LAB/("moe_upstream_"+a.run_id+".json")
 logfile=LAB/("moe_upstream_"+a.run_id+".log")
 if report.exists() or logfile.exists():ap.error("REFUSE_OVERWRITE_IMMUTABLE_TRIAL")
 result={"run_id":a.run_id,"engine":a.engine,"model":a.model,"mode":a.mode,"executed":False,
         "default_production_unchanged":True,"rows":[]}
 def save():report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 try:
  start=preflight(a.model,a.engine,a.mode)
  result["preflight"]=start
  result["status"]="blocked_preflight" if not start["admitted"] else "eligible_not_executed"
  if not a.execute or not start["admitted"]:
   save();print(json.dumps({"status":result["status"],"reasons":start.get("reasons"),"path":str(report)}));return
  fd=os.open(str(LOCK),os.O_CREAT|os.O_RDWR,0o660);child=None;flag=threading.Event();watcher=None
  try:
   try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:
    result["status"]="gpu_lock_busy";save();return
   second=preflight(a.model,a.engine,a.mode)
   result["second_preflight"]=second
   if not second["admitted"]:
    result["status"]="blocked_after_lock";save();return
   bin=BINARIES[a.engine];model=MODELS[a.model]
   cmd=[str(bin),"-m",str(model),"-ngl","99","--n-cpu-moe","0","--fit","off","-c","8192",
        "-np","1","-fa","on","-b","512","-ub","128","-t","8","-tb","8",
        "-ctk","f16","-ctv","f16","--host","127.0.0.1","--port","18139","--no-webui",
        "--no-warmup","--reasoning","off","--alias","Cloud9-MoE-Upstream-LAB"]
   if a.mode=="mtp2":cmd+=["--spec-type","draft-mtp","--spec-draft-n-max","2"]
   result["cli_flags"]=cmd[1:][::] # report includes only filesystem paths and flags, no secrets
   with logfile.open("x") as log:
    child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
    result["status"]="loading";save()
    guard_events=[]
    def watch():
     while not flag.wait(2):
      try:
       g=guardian(0);t=host_temp()
       if g.get("psi_memory_full_avg10",99)>=1.8 or g.get("mem_available_gib",0)<20.5 or g.get("swap_used_percent",100)>95 or t is None or t>=80:
        guard_events.append({"reason":"RUNTIME_PRESSURE","guardian":g,"temp_c":t});stop_own(child);return
      except Exception as e:
       guard_events.append({"reason":"GUARD_UNAVAILABLE","error_type":type(e).__name__});stop_own(child);return
    watcher=threading.Thread(target=watch,daemon=True);watcher.start()
    ready=False;ts=time.monotonic()
    for _ in range(100):
     if child.poll() is not None or guard_events:break
     try:
      if fetch(URL+"/health",timeout=1).get("status")=="ok":ready=True;break
     except Exception:pass
     time.sleep(.6)
    result["load_s"]=round(time.monotonic()-ts,3)
    if not ready:
     result["status"]="failed_load_or_guard";result["guard_events"]=guard_events;save();return
    result["executed"]=True;result["status"]="running";save()
    for name,prompt in PROMPTS:
     g=guardian(0);temp=host_temp()
     if g.get("psi_memory_full_avg10",99)>=.5 or g.get("mem_available_gib",0)<21 or temp is None or temp>=78:
      result["status"]="paused_runtime_pressure";result["guard_events"]=guard_events;save();return
     ts=time.monotonic()
     payload={"model":"Cloud9-MoE-Upstream-LAB","temperature":0,"seed":42,
              "stream":False,"max_tokens":256,"messages":[{"role":"user","content":prompt}]}
     try:reply=fetch(URL+"/v1/chat/completions",payload,timeout=180)
     except Exception as e:
      result["status"]="failed_request";result["error_type"]=type(e).__name__;save();return
     usage=reply.get("usage") or {}
     timings=reply.get("timings") or {}
     text=str((reply.get("choices") or [{}])[0].get("message",{}).get("content",""))
     result["rows"].append({"task":name,"wall_s":round(time.monotonic()-ts,3),
                           "prompt_tokens":usage.get("prompt_tokens"),"completion_tokens":usage.get("completion_tokens"),
                           "timings":timings,"text_sha256":hashlib.sha256(text.encode()).hexdigest(),
                           "nonempty":bool(text.strip())})
     save()
    result["status"]="complete" if len(result["rows"])==3 and all(x["nonempty"] for x in result["rows"]) else "failed_quality"
    result["guard_events"]=guard_events;save()
  finally:
   flag.set();stop_own(child)
   if watcher:watcher.join(timeout=3)
   fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)
   if 'guard_events' in locals() and guard_events:
    result["status"]="failed_watchdog";result["guard_events"]=guard_events;save()
 except Exception as e:
  result["status"]="failed_exception";result["error_type"]=type(e).__name__;save();raise

if __name__=="__main__":main()
