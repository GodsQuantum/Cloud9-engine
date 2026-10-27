#!/usr/bin/env python3
"""Read-only, thermal-guarded synthetic multi-position context retrieval for Cloud9.

Requires an EXTERNAL CT410 GPU lease + official memory admission.
Starts ONLY a selected test llama-server on CT700. Never modifies production.
"""
import argparse
import hashlib
import json
import os
import random
import re
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT=Path("/home/arezki/Projets/HomeLab/Moteurs IA")
OUT=ROOT/"Sources/Benchmarks/Engine-Tournament/2026-10-22"
MODEL=Path("/srv/storage/nvme/shared/ai-models/llm/gguf/Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf")
ENGINE=ROOT/"Sources/Builds/atomic-turboquant-2.0.0-20261016/build-cloud9/bin/llama-server"
PORT=18227
CODES={"alpha":"VTR-9385","beta":"MQR-5281","gamma":"BDV-1947","delta":"JKP-6032","omega":"FNC-7824"}
WRITTEN=["matrice", "dossier", "archive", "équipement", "spécification", "métrique",
         "contrôle", "validation", "analyse", "document", "opération", "hypothèse",
         "rapport", "procédure", "récupération", "index", "cohérence", "calcul"]
def api(endpoint,body=None,seconds=120):
    payload=json.dumps(body,ensure_ascii=False).encode() if body is not None else None
    req=urllib.request.Request("http://127.0.0.1:"+str(PORT)+endpoint,data=payload,
       headers={"Content-Type":"application/json"} if payload else {})
    with urllib.request.urlopen(req,timeout=seconds) as response:return json.load(response)
def stop(proc):
    if proc is not None and proc.poll() is None:
        os.killpg(proc.pid,signal.SIGTERM)
        try:proc.wait(timeout=12)
        except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=8)
def temperature():
    for p in Path("/sys/class/hwmon").glob("hwmon*/name"):
        try:
            if p.read_text().strip()=="k10temp":
                return int((p.parent/"temp1_input").read_text())/1000
        except (OSError,ValueError):pass
    raise RuntimeError("Missing Tctl")
def mktext(repeats):
    chunks=[]
    for i,(name,code) in enumerate(CODES.items()):
        group=[]
        for j in range(repeats):
            rng=random.Random(1299+i*4301+j)
            words=" ".join(rng.choice(WRITTEN) for _ in range(34))
            group.append(f"Dossier fictif {i}-{j:04d}. Texte artificiel sans données utilisateur. {words}. Note de contrôle numérotée {j} : ordres, index et descriptions du stock synthétique.\n")
        group.insert(len(group)//2,f"REGISTRE_VALIDÉ_{name.upper()} : identifiant exact {code}. Ne le modifie pas. Ceci est l'entrée {name} dans le document.\n")
        chunks.extend(group)
    prefix="DOSSIER ENTIEREMENT SYNTHETIQUE — pour une évaluation de récupération dans un contexte long. Tous les noms et codes sont fictifs.\n"
    ending="\nRéponds uniquement par un objet JSON strict, sans Markdown, contenant EXACTEMENT les clés alpha, beta, gamma, delta, omega. Chaque valeur doit être l'identifiant exact de la ligne REGISTRE_VALIDÉ correspondante du dossier. N'invente pas de codes.\n"
    return prefix+"".join(chunks)+ending
def measured(n):
    text=mktext(n)
    ans=api("/tokenize",{"content":text,"add_special":False},seconds=35)
    tokens=ans.get("tokens")
    if not isinstance(tokens,list):raise RuntimeError("Tokenizer response did not provide token IDs")
    return len(tokens),text
def build_target(target):
    n=15
    for _ in range(5):
        got,_=measured(n)
        n=max(2,min(400,round(n*target/max(got,1))))
        if abs(got-target)/target<=.035:break
    got,text=measured(n)
    if not .90*target<=got<=1.06*target:
        raise RuntimeError(f"TARGET_NOT_ACCURATE goal={target} actual={got}")
    return got,text
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--target",type=int,choices=[8192,16384,32768,65536,131072,262144,524288,1048576],required=True)
    ap.add_argument("--reps",type=int,default=3)
    a=ap.parse_args()
    assert os.environ.get("CLOUD9_GPU_COEXIST_ADMITTED")=="1"
    assert a.reps>=3
    assert MODEL.is_file() and ENGINE.is_file() and temperature()<75
    capacity=min(max(12288,round(a.target*1.35)),1048576+8192)
    assert capacity>=a.target+512
    base=f"atomic-turboquant2-qwen4b-mtp2-q8turbo3-needle5-{a.target}-reps{a.reps}"
    out=OUT/(base+".json")
    workerlog=OUT/(base+".server.log")
    assert not out.exists() and not workerlog.exists()
    OUT.mkdir(parents=True,exist_ok=True)
    result={"status":"not_started","date":time.strftime("%Y-%m-%dT%H:%M:%S%z"),
       "model":MODEL.name,"engine":"Atomic TurboQuant 2.0.0 Vulkan RADV gfx1103",
       "target_tokens":a.target,"ctx_allocated":capacity,
       "native_mtp":"draft-mtp n-max2","kv_k":"q8_0","kv_v":"turbo3",
       "repetitions_requested":a.reps,"no_context_shift":True,
       "expected":CODES,"rows":[],"long_context_pass":False}
    p=None
    try:
        with workerlog.open("x") as stream:
            cmd=[str(ENGINE),"-m",str(MODEL),"--host","127.0.0.1","--port",str(PORT),"-c",str(capacity),
                "-ngl","99","-np","1","-b","512","-ub","512","--flash-attn","on","--fit","off",
                "--no-warmup","--no-webui","--no-context-shift","--jinja","--reasoning","off",
                "--reasoning-budget","0","-ctk","q8_0","-ctv","turbo3",
                "--spec-type","draft-mtp","--spec-draft-n-max","2"]
            p=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,
                env={**os.environ,"LD_LIBRARY_PATH":str(ENGINE.parent)+":"+os.environ.get("LD_LIBRARY_PATH","")})
            for _ in range(150):
                if p.poll() is not None:raise RuntimeError("SERVER_CRASHED rc="+str(p.returncode))
                try:
                    if api("/health",seconds=2).get("status")=="ok":break
                except Exception:pass
                time.sleep(.4)
            else:raise RuntimeError("HEALTH_TIMEOUT")
            tokens,text=build_target(a.target)
            result["measured_token_count_by_tokenizer"]=tokens
            result["fixture_sha256"]=hashlib.sha256(text.encode()).hexdigest()
            print("MODEL_READY target",a.target,"actual",tokens,"ctx",capacity,flush=True)
            for rep in range(1,a.reps+1):
                before=temperature()
                if before>=75:raise RuntimeError(f"TOO_HOT_BEFORE_REPEAT_{rep}: {before}")
                body={"model":str(MODEL),"messages":[{"role":"user","content":text}],
                       "seed":42+rep,"temperature":0,"max_tokens":160,"stream":False,
                       "cache_prompt":False,"enable_thinking":False}
                start=time.monotonic()
                data=api("/v1/chat/completions",body,seconds=270)
                wall=time.monotonic()-start
                content=(data["choices"][0]["message"].get("content") or "").strip()
                try:prediction=json.loads(content)
                except (ValueError,TypeError):prediction=None
                valid=prediction==CODES
                timing=data.get("timings") or {}
                usage=data.get("usage") or {}
                actual=usage.get("prompt_tokens")
                if actual is None or actual<.9*a.target:
                    raise RuntimeError("NO_PROOF_FULL_PROMPT_INGESTION actual="+str(actual))
                row={"rep":rep,"prompt_tokens_observed":actual,"correct_all_five":valid,
                     "correct_markers":sum(prediction.get(k)==v for k,v in CODES.items()) if isinstance(prediction,dict) else 0,
                     "duration_s":round(wall,3),"prefill_tps":timing.get("prompt_per_second"),
                     "decode_tps":timing.get("predicted_per_second"),
                     "draft_accepted":timing.get("draft_n_accepted",timing.get("draft_accepted")),
                     "draft_proposed":timing.get("draft_n"),
                     "tctl_before":before,"tctl_after":temperature(),
                     "answer_sha256":hashlib.sha256(content.encode()).hexdigest()}
                result["rows"].append(row)
                out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
                print("NEEDLE5",json.dumps(row),flush=True)
                if temperature()>=77.5:raise RuntimeError("HOT_AFTER_PROMPT_STOP")
                if rep<a.reps:
                    coolstart=time.monotonic()
                    while temperature()>68.5 and time.monotonic()-coolstart<65:time.sleep(4)
                    if temperature()>74:raise RuntimeError("NO_COOLING")
            result["long_context_pass"]=all(x["correct_all_five"] for x in result["rows"])
            result["status"]="retrieval_pass" if result["long_context_pass"] else "retrieval_quality_failed"
    except Exception as e:
        result["status"]="incomplete_or_blocked"
        result["error"]=repr(e)
        print("NEEDLE_CONTEXT_ERROR",repr(e),flush=True)
    finally:
        stop(p)
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        print("NEEDLE_CONTEXT_ENDED",result["status"],"rows",len(result["rows"]),str(out),flush=True)
    if result["status"]!="retrieval_pass":raise SystemExit(4)
if __name__=="__main__":main()
