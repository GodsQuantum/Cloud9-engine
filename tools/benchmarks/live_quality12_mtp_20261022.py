#!/usr/bin/env python3
"""Execute 36 simulated read-only quality calls against ONE native-MTP candidate.

MUST be run under CT410's external official memory admission / GPU lock /
thermal watchdog. No real tools are ever executed. No production writes.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT=Path("/home/arezki/Projets/HomeLab/Moteurs IA")
PARENT=ROOT/"Sources/Builds"
STORE=Path("/srv/storage/nvme/shared/ai-models/llm/gguf")
OUT=ROOT/"Sources/Benchmarks/Engine-Tournament/2026-10-22"
PORT=18229
GRADER=Path(__file__).resolve().with_name("one_engine_quality_protocol_20261022.py")
CANDIDATES={
 "atomic4b":{
  "bin":PARENT/"atomic-turboquant-2.0.0-20261016/build-cloud9/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","turbo3"],
  "expected_bytes":2790000800
 },
 "b11798-9b":{
  "bin":PARENT/"llama-b11798-codespace-20261022/bin/llama-server",
  "model":STORE/"Qwen3.8-9B-Distill-Heretic-Uncensored-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","f16","-ctv","f16"],
  "expected_bytes":5780090624
 }
}
def api(path,payload=None,timeout=120):
    data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
    req=urllib.request.Request(f"http://127.0.0.1:{PORT}{path}",
        data=data,headers={"Content-Type":"application/json"} if data else {})
    with urllib.request.urlopen(req,timeout=timeout) as response:return json.load(response)
def tctl():
    for p in Path("/sys/class/hwmon").glob("hwmon*/name"):
        try:
            if p.read_text().strip()=="k10temp":return int((p.parent/"temp1_input").read_text())/1000
        except (OSError,ValueError):pass
    raise RuntimeError("No k10temp Tctl")
def stop(p):
    if p and p.poll() is None:
        os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=12)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",choices=sorted(CANDIDATES),required=True)
    p.add_argument("--reps",type=int,default=3)
    args=p.parse_args()
    assert os.environ.get("CLOUD9_GPU_COEXIST_ADMITTED")=="1"
    assert args.reps>=3 and tctl()<75
    spec=CANDIDATES[args.candidate]
    path=spec["model"]
    binary=spec["bin"]
    assert binary.is_file() and path.is_file() and path.stat().st_size==spec["expected_bytes"]
    assert GRADER.is_file()
    mod=importlib.util.spec_from_file_location("one_engine_quality_protocol",GRADER)
    grade=importlib.util.module_from_spec(mod);mod.loader.exec_module(grade)
    tag=f"{args.candidate}-quality12x{args.reps}-mtp2-20261022"
    result_path=OUT/(tag+".json")
    log_path=OUT/(tag+".server.log")
    assert not result_path.exists() and not log_path.exists()
    OUT.mkdir(parents=True,exist_ok=True)
    result={
      "status":"starting","date":time.strftime("%Y-%m-%dT%H:%M:%S%z"),
      "candidate":args.candidate,"engine_sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),
      "model":path.name,"model_bytes":path.stat().st_size,
      "native_speculation":"draft-mtp","native_spec_draft_max":2,
      "backend":"Cloud9 Radeon 780M Vulkan gfx1103",
      "protocol":grade.PROTOCOL,"repetitions_requested":args.reps,
      "quality_run_kind":"synthetic fictitious tools, code, French, strict JSON, editorial pending",
      "rows":[],"production_eligible":False}
    server=None
    try:
        with log_path.open("x") as stream:
            cmd=[str(binary),"-m",str(path),"--host","127.0.0.1","--port",str(PORT),
               "-ngl","99","-np","1","-b","512","-ub","512","--flash-attn","on",
               "--fit","off","--no-warmup","--no-webui","--no-context-shift",
               "--jinja","--reasoning","off","--reasoning-budget","0",
               "--spec-type","draft-mtp","--spec-draft-n-max","2"]+spec["flags"]
            server=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,
               env={**os.environ,"LD_LIBRARY_PATH":str(binary.parent)+":"+os.environ.get("LD_LIBRARY_PATH","")},
               start_new_session=True)
            started=time.monotonic()
            for i in range(150):
                if server.poll() is not None:raise RuntimeError("MODEL_START_EXIT rc="+str(server.returncode))
                try:
                    if api("/health",timeout=2).get("status")=="ok":break
                except Exception:pass
                time.sleep(.3)
            else:raise RuntimeError("MODEL_HEALTH_TIMEOUT")
            result["load_s"]=round(time.monotonic()-started,3)
            print("QUALITY_MODEL_READY",args.candidate,"load",result["load_s"],flush=True)
            for rep in range(1,args.reps+1):
                for case in grade.CASES:
                    if tctl()>=75:raise RuntimeError("TEMPERATURE_PRE_CASE_EXCEEDS_75C")
                    payload=grade.request(case["id"],str(path),rep)
                    payload["cache_prompt"]=False
                    payload["enable_thinking"]=False
                    t0=time.monotonic()
                    try:
                        data=api("/v1/chat/completions",payload,timeout=110)
                        msg=data["choices"][0]["message"]
                        e=None
                    except Exception as exc:
                        data={}
                        msg={}
                        e=repr(exc)
                    wall=time.monotonic()-t0
                    grading=grade.grade(case["id"],msg)
                    timing=data.get("timings") or {}
                    usage=data.get("usage") or {}
                    row={"id":case["id"],"kind":case["kind"],"rep":rep,
                       "correct":grading["correct"],"editorial_review_pending":grading["editorial_pending"],
                       "error":e,"message":msg,"wall_s":round(wall,4),
                       "prompt_tokens":usage.get("prompt_tokens"),
                       "completion_tokens":usage.get("completion_tokens"),
                       "prefill_tps":timing.get("prompt_per_second"),
                       "decode_tps":timing.get("predicted_per_second"),
                       "draft_accepted":timing.get("draft_n_accepted",timing.get("draft_accepted")),
                       "draft_proposed":timing.get("draft_n"),
                       "temp_after":tctl()}
                    result["rows"].append(row)
                    result_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
                    print("QUALITY_CASE",case["id"],rep,"correct",row["correct"],"wall",row["wall_s"],flush=True)
                    if row["temp_after"]>=77.5:raise RuntimeError("HOT_AFTER_CASE")
                    if e:raise RuntimeError("API_REQUEST_FAILED "+e)
            s=grade.aggregate(result["rows"],args.reps)
            result["quality"]=s["quality"]
            result["status"]="complete_editorial_review_pending"
    except Exception as exc:
        result["status"]="incomplete_or_error"
        result["error"]=repr(exc)
        print("QUALITY_ABORT",repr(exc),flush=True)
    finally:
        stop(server)
        result_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        print("QUALITY_DONE",result["status"],"rows",len(result["rows"]),result_path,flush=True)
    if result["status"]!="complete_editorial_review_pending":raise SystemExit(4)
if __name__=="__main__":main()
