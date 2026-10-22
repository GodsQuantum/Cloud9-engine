#!/usr/bin/env python3
"""Magnitude 0.2.10 Vulkan + Qwen35 dense embedded MTP: isolated Cloud9 GPU test.

Needs pre-held official CT410 GPU arbitration lease. Contains no real tools,
user data, external credentials, service mutation or model downloads.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT=Path("/home/arezki/Projets/HomeLab/Moteurs IA")
BIN=ROOT/"Sources/Builds/magnitude-v0210-codespace-release/magnitude-engine"
MODEL=Path("/srv/storage/nvme/shared/ai-models/llm/gguf/Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf")
DIR=ROOT/"Sources/Benchmarks/Engine-Tournament/2026-10-22"
PORT=18230
LEGACY=ROOT/"Sources/Benchmarks/Engine-Tournament/2026-10-18/vulkan_agentic_mtp_2tokens_A_B.py"
def api(endpoint,payload=None,timeout=12):
    content=json.dumps(payload,ensure_ascii=False).encode("utf8") if payload is not None else None
    req=urllib.request.Request(f"http://127.0.0.1:{PORT}"+endpoint,
       data=content,headers={"Content-Type":"application/json"} if content else {})
    with urllib.request.urlopen(req,timeout=timeout) as reply:return json.load(reply)
def tctl():
    for p in Path("/sys/class/hwmon").glob("hwmon*/name"):
        try:
            if p.read_text().strip()=="k10temp":return int((p.parent/"temp1_input").read_text())/1000
        except (OSError,ValueError):pass
    raise RuntimeError("Missing thermal sensor")
def stop(p):
    if p is not None and p.poll() is None:
        os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=12)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--reps",type=int,default=3)
    a=parser.parse_args()
    assert a.reps>=3 and os.environ.get("CLOUD9_GPU_COEXIST_ADMITTED")=="1"
    assert BIN.is_file() and MODEL.is_file() and MODEL.stat().st_size==2790000800
    assert tctl()<75
    spec=importlib.util.spec_from_file_location("quality",LEGACY)
    legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    cases=legacy.cases()
    tag=f"magnitude-v0210-Qwen35dense4B-MTP2-Vulkan-all-reps{a.reps}-v2"
    OUT=DIR/(tag+".json")
    LOG=DIR/(tag+".server.log")
    assert not OUT.exists() and not LOG.exists()
    DIR.mkdir(parents=True,exist_ok=True)
    result={"date":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"status":"starting",
       "engine":"Magnitude v0.2.10 native Vulkan","engine_sha256":hashlib.sha256(BIN.read_bytes()).hexdigest(),
       "gguf":MODEL.name,"model_size_bytes":MODEL.stat().st_size,
       "gpu":"AMD Radeon 780M / gfx1103","method":"mtp","mtp_proposals":2,
       "device":"vulkan","context":4096,"kv_codec":"dense",
       "output_capacity":256,"prefill_tokens":512,
       "test_protocol":"legacy 2026-10-18 synthetic five cases read-only, 3 repeats",
       "repetitions":a.reps,"rows":[],"no_production_change":True}
    worker=None
    try:
        with LOG.open("x") as stream:
            cmd=[str(BIN),"--model",str(MODEL),
                 "--host","127.0.0.1","--port",str(PORT),
                 "--context-tokens","4096","--output-capacity","256",
                 "--prefill-tokens","512","--method","mtp","--mtp-proposals","2",
                 "--kv-codec","dense","--device","vulkan",
                 "--tuning-budget","2","--cache-dir","/tmp/cloud9-magnitude-20261022-qwen4b"]
            result["cmd_flags"]=cmd[1:]
            worker=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            begin=time.monotonic()
            for trial in range(180):
                if worker.poll() is not None:raise RuntimeError("ENGINE_EXITED rc="+str(worker.returncode))
                try:
                    for endpoint in ("/health","/v1/models"):
                        try:
                            health=api(endpoint,timeout=2)
                            if isinstance(health,dict) and health.get("status") in ("ok","ready"):
                                break
                            if "data" in health or "models" in health:
                                break
                        except (OSError,ValueError,urllib.error.HTTPError):
                            continue
                    else:
                        time.sleep(.5);continue
                    break
                except Exception:
                    time.sleep(.5)
            else:raise RuntimeError("STARTUP_HEALTH_TIMEOUT")
            result["load_s"]=round(time.monotonic()-begin,2)
            print("MAGNITUDE_LOADED",result["load_s"],flush=True)
            for rep in range(1,a.reps+1):
                for name,fixture in cases.items():
                    if tctl()>=75:raise RuntimeError("TEMPERATURE_TOO_HIGH")
                    body={"model":str(MODEL),"seed":42,"temperature":0,"stream":False,
                        "enable_thinking":False,"cache_prompt":False,**fixture}
                    begin=time.monotonic()
                    answer=api("/v1/chat/completions",body,timeout=120)
                    latency=time.monotonic()-begin
                    message=answer["choices"][0]["message"]
                    timings=answer.get("timings") or {}
                    usage=answer.get("usage") or {}
                    row={"kind":name,"rep":rep,"correct":legacy.correct(name,message),
                        "wall_s":round(latency,4),"prompt_tokens":usage.get("prompt_tokens"),
                        "completion_tokens":usage.get("completion_tokens"),
                        "decode_tps_native":timings.get("predicted_per_second"),
                        "prefill_tps_native":timings.get("prompt_per_second"),
                        "draft_proposed":timings.get("draft_n"),
                        "draft_accepted":timings.get("draft_n_accepted",timings.get("draft_accepted")),
                        "end_to_end_effective_tps":round(usage.get("completion_tokens",0)/latency,3) if latency>0 else None,
                        "tctl_after":tctl(),
                        "message":message}
                    result["rows"].append(row)
                    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
                    print("MAGNITUDE_TEST",name,rep,row["correct"],row["wall_s"],flush=True)
                    if row["tctl_after"]>=77.5:raise RuntimeError("THERMAL_CEILING")
            result["status"]="complete"
    except Exception as e:
        result["status"]="error_or_partial"
        result["error"]=repr(e)
        print("MAGNITUDE_TEST_FAIL",repr(e),flush=True)
        if LOG.exists():
            result["log_tail"]=LOG.read_text(errors="replace")[-4000:]
    finally:
        stop(worker)
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        print("MAGNITUDE_RUN_END",result["status"],"rows",len(result["rows"]),OUT,flush=True)
    if result["status"]!="complete":raise SystemExit(4)
if __name__=="__main__":main()
