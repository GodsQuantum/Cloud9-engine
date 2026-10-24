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
 "atomic4b-hip-turbo3":{
  "bin":PARENT/"atomic-turboquant-2.0.0-rocm-20261023/build/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","turbo3"],
  "expected_bytes":2790000800
 },
 "atomic4b-hip-q8v":{
  "bin":PARENT/"atomic-turboquant-2.0.0-rocm-20261023/build/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "expected_bytes":2790000800
 },
 "atomic4b-q8v":{
  "bin":PARENT/"atomic-turboquant-2.0.0-20261016/build-cloud9/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "expected_bytes":2790000800
 },
 "rdna-r111-hip-4b":{
  "bin":PARENT/"llama-rdna-r111-hip-gfx1103-actions-20261023/rdna-hip-artifact/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "expected_bytes":2790000800
 },
 "rdna-r111-vulkan-4b":{
  "bin":PARENT/"llama-rdna-r111-vulkan-gfx1103-20261022/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "expected_bytes":2790000800
 },
 "rdna-r120-hip-4b":{
  "bin":PARENT/"latest-rdna-r120-hip-20261023/rdna-hip-artifact/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "expected_bytes":2790000800
 },
 "upstream-master-4b":{
  "bin":PARENT/"latest-upstream-master062-vulkan-20261023/package/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "expected_bytes":2790000800
 },
 "s1-head-4b":{
  "bin":PARENT/"latest-s1-vulkan-20261023/package/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "expected_bytes":2790000800
 },
 "prism-head-4b":{
  "bin":PARENT/"latest-prism-vulkan-20261023/package/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "expected_bytes":2790000800
 },
 "chimera-062-mmb-off":{
  "bin":PARENT/"latest-chimera-mmb-r120-on-master062-hip-20261023/chimera-uncertified/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "env":{"GGML_CUDA_MMB":"0","GGML_CUDA_MMB_RDNA3":"1","GGML_CUDA_MMF32":"0"},
  "backend":"HIP",
  "expected_bytes":2790000800
 },
 "chimera-062-mmb-on":{
  "bin":PARENT/"latest-chimera-mmb-r120-on-master062-hip-20261023/chimera-uncertified/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "env":{"GGML_CUDA_MMB":"1","GGML_CUDA_MMB_RDNA3":"1","GGML_CUDA_MMF32":"0"},
  "backend":"HIP",
  "expected_bytes":2790000800
 },
 "chimera-062-mmb-mmf32":{
  "bin":PARENT/"latest-chimera-mmb-r120-on-master062-hip-20261023/chimera-uncertified/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "env":{"GGML_CUDA_MMB":"1","GGML_CUDA_MMB_RDNA3":"1","GGML_CUDA_MMF32":"1"},
  "backend":"HIP",
  "expected_bytes":2790000800
 },
 "upstream-062-hip-4b":{
  "bin":PARENT/"latest-upstream-master062-hip-20261023/package/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "backend":"HIP",
  "expected_bytes":2790000800
 },
 "b11798-4b":{
  "bin":PARENT/"llama-b11798-codespace-20261022/bin/llama-server",
  "model":STORE/"Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "expected_bytes":2790000800
 },
 "b11798-35b":{
  "bin":PARENT/"llama-b11798-codespace-20261022/bin/llama-server",
  "model":STORE/"Qwen3.6-35B-A3B-Pym-Q2-MTP.gguf",
  "flags":["-c","4096","-ctk","q8_0","-ctv","q8_0"],
  "expected_bytes":13222476000
 },
 "b11798-hermes9b":{
  "bin":PARENT/"llama-b11798-codespace-20261022/bin/llama-server",
  "model":STORE/"qwen3.8-9b-hermes-fc-tooluse.Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","q8_0","-ctv","q8_0"],
  "expected_bytes":5778720640
 },
 "b11798-9b":{
  "bin":PARENT/"llama-b11798-codespace-20261022/bin/llama-server",
  "model":STORE/"Qwen3.8-9B-Distill-Heretic-Uncensored-MTP-Q4_K_M.gguf",
  "flags":["-c","8192","-ctk","f16","-ctv","f16"],
  "expected_bytes":5780090624
 }
}
# Historical CANDIDATES remain inspectable for evidence parsing only.
# Never allow a new live GPU run against retired b11798 or r111.
LATEST_ONLY_CANDIDATES=frozenset({
    "atomic4b", "atomic4b-q8v", "atomic4b-hip-turbo3", "atomic4b-hip-q8v",
    "rdna-r120-hip-4b", "upstream-master-4b", "prism-head-4b", "s1-head-4b",
    "chimera-062-mmb-off", "chimera-062-mmb-on", "chimera-062-mmb-mmf32", "upstream-062-hip-4b",
})
assert LATEST_ONLY_CANDIDATES <= set(CANDIDATES)
LATEST_SOURCE_MANIFEST=Path(__file__).with_name("latest_engine_sources_20261023.json")

def validate_latest_only(candidate, *, live_api=None, _test_skip_binary_sha=False):
    """Recheck official upstream refs/releases NOW, fail closed before GPU use.

    `live_api` is injectable solely to run deterministic offline contract tests.
    """
    assert candidate in LATEST_ONLY_CANDIDATES, f"RETIRED_ENGINE_GPU_TEST_DENIED: {candidate}"
    lock=json.loads(LATEST_SOURCE_MANIFEST.read_text())
    import importlib.util
    path=Path(__file__).with_name("verify_latest_sources.py")
    spec=importlib.util.spec_from_file_location("cloud9_latest_freshness",path)
    gate=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    attestation=gate.verify_candidate(candidate,lock,
        api=gate.github_api if live_api is None else live_api)
    if candidate.startswith("chimera-062-"):
        # A native hybrid MUST revalidate BOTH contemporary source branches,
        # never accept only the trunk while the RDNA donor advances.
        attestation["rdna_donor"]=gate.verify_one("rdna",lock["github_repositories"]["rdna"],
             gate.github_api if live_api is None else live_api)
    if not _test_skip_binary_sha:
        expected_sha=lock.get("lab_candidate_binary_sha256",{}).get(candidate)
        if not isinstance(expected_sha,str) or len(expected_sha)!=64:
            raise gate.UnverifiedSource(f"LATEST_BINARY_SHA_NOT_CERTIFIED {candidate}")
        path=CANDIDATES[candidate]["bin"]
        if not path.is_file():
            raise gate.UnverifiedSource(f"LATEST_BINARY_MISSING {candidate}")
        actual_sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_sha!=expected_sha:
            raise gate.StaleSource(f"LATEST_BINARY_SHA_MISMATCH_REBUILD {candidate}")
        attestation["binary_sha256"]=actual_sha
    lock["_freshness_attestation"]=attestation
    return lock

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
def prepare_resume(previous,expected,cases,reps):
    """Validate and resume only a matching interrupted session.

    This is deliberately pure: no GPU, filesystem or network side effects.
    """
    assert previous.get("status") in ("starting","resuming","incomplete_or_error"),"completed evidence may not be resumed"
    assert all(previous.get(key)==value for key,value in expected.items()),"evidence/model/protocol mismatch"
    allowed={(rep,case["id"]) for rep in range(1,reps+1) for case in cases}
    completed=set();valid=[];failed=[]
    for row in previous.get("rows",[]):
        ident=(row.get("rep"),row.get("id"))
        assert ident in allowed,"invalid stored trial identifier"
        assert ident not in completed and not any((x["rep"],x["id"])==ident for x in failed),"duplicate stored trial identifier"
        if row.get("error"):
            failed.append(row)
        else:
            valid.append(row)
            completed.add(ident)
    assert len(completed)<len(allowed),"all trials already present"
    previous["rows"]=valid
    if failed:previous.setdefault("retry_history",[]).extend(failed)
    previous.pop("error",None)
    previous["status"]="resuming"
    previous["resume_valid_cases"]=len(completed)
    return previous,completed

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",choices=sorted(LATEST_ONLY_CANDIDATES),required=True)
    p.add_argument("--reps",type=int,default=3)
    p.add_argument("--thermal-pace",action="store_true",help="Cool to <=72 C between requests; does not alter speed measurement per API response")
    p.add_argument("--trial-tag",default="",help="New suffix for immutable A/B evidence; lowercase letters, digits, hyphen")
    p.add_argument("--resume",action="store_true",help="Resume only a matching incomplete recorded benchmark, without rerunning valid cases")
    args=p.parse_args()
    latest_lock=validate_latest_only(args.candidate)
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
    if args.thermal_pace:tag+="-thermalpaced-v2"
    if args.trial_tag:
        import re
        assert re.fullmatch(r"[a-z0-9-]{1,48}",args.trial_tag),"invalid trial suffix"
        tag+="-"+args.trial_tag
    result_path=OUT/(tag+".json")
    log_path=OUT/(tag+".server.log")
    if args.resume:
        assert result_path.is_file() and log_path.is_file(),"cannot resume without existing evidence"
    else:
        assert not result_path.exists() and not log_path.exists(),"immutable benchmark evidence already exists"
    OUT.mkdir(parents=True,exist_ok=True)
    result={
      "status":"starting","date":time.strftime("%Y-%m-%dT%H:%M:%S%z"),
      "candidate":args.candidate,"engine_sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),
      "model":path.name,"model_bytes":path.stat().st_size,
      "native_speculation":"draft-mtp","native_spec_draft_max":2,
      "backend":"Cloud9 Radeon 780M "+spec.get("backend",("HIP" if "hip" in args.candidate else "Vulkan"))+" gfx1103",
      "ablation_environment":spec.get("env",{}),
      "source_version_lock_sha256":hashlib.sha256(LATEST_SOURCE_MANIFEST.read_bytes()).hexdigest(),
      "source_freshness_attestation":latest_lock["_freshness_attestation"],
      "protocol":grade.PROTOCOL,"repetitions_requested":args.reps,
      "quality_run_kind":"synthetic fictitious tools, code, French, strict JSON, editorial pending",
      "rows":[],"production_eligible":False}
    completed=set()
    if args.resume:
        expected={"candidate":args.candidate,"engine_sha256":result["engine_sha256"],
                  "model":path.name,"model_bytes":path.stat().st_size,
                  "repetitions_requested":args.reps,"protocol":grade.PROTOCOL}
        result,completed=prepare_resume(json.loads(result_path.read_text()),
                                        expected,grade.CASES,args.reps)
    def save_result():
        tmp=result_path.with_suffix(".json.pending")
        tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        tmp.replace(result_path)
    server=None
    try:
        with log_path.open("a" if args.resume else "x") as stream:
            if args.resume:
                stream.write("\n=== RESUME candidate "+args.candidate+" rows="+str(len(completed))+" ===\n")
                stream.flush()
            cmd=[str(binary),"-m",str(path),"--host","127.0.0.1","--port",str(PORT),
               "-ngl","99","-np","1","-b","512","-ub","512","--flash-attn","on",
               "--fit","off","--no-warmup","--no-webui","--no-context-shift",
               "--jinja","--reasoning","off","--reasoning-budget","0",
               "--spec-type","draft-mtp","--spec-draft-n-max","2"]+spec["flags"]
            server=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,
               env={**os.environ,"LD_LIBRARY_PATH":str(binary.parent)+":"+os.environ.get("LD_LIBRARY_PATH",""),**spec.get("env",{})},
               start_new_session=True)
            started=time.monotonic()
            for i in range(150):
                if server.poll() is not None:raise RuntimeError("MODEL_START_EXIT rc="+str(server.returncode))
                try:
                    if api("/health",timeout=2).get("status")=="ok":break
                except Exception:pass
                time.sleep(.3)
            else:raise RuntimeError("MODEL_HEALTH_TIMEOUT")
            current_load_s=round(time.monotonic()-started,3)
            if not args.resume:result["load_s"]=current_load_s
            result.setdefault("sessions",[]).append({"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
                "load_s":current_load_s,"resumed":args.resume,"preexisting_cases":len(completed)})
            print("QUALITY_MODEL_READY",args.candidate,"load",current_load_s,"resumed",args.resume,flush=True)
            for rep in range(1,args.reps+1):
                for case in grade.CASES:
                    if (rep,case["id"]) in completed:continue
                    if args.thermal_pace:
                        limit=time.monotonic()+120
                        while tctl()>72.0:
                            if time.monotonic()>=limit:raise RuntimeError("TEMPERATURE_COOLDOWN_TIMEOUT")
                            time.sleep(3)
                    elif tctl()>=75:raise RuntimeError("TEMPERATURE_PRE_CASE_EXCEEDS_75C")
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
                    save_result()
                    print("QUALITY_CASE",case["id"],rep,"correct",row["correct"],"wall",row["wall_s"],flush=True)
                    if row["temp_after"]>=77.5:raise RuntimeError("HOT_AFTER_CASE")
                    if e:raise RuntimeError("API_REQUEST_FAILED "+e)
            s=grade.aggregate(result["rows"],args.reps)
            result["quality"]=s["quality"]
            # Revalidate after GPU run. A newly published release/HEAD makes
            # otherwise valid evidence historical, NEVER a current champion.
            final_lock=validate_latest_only(args.candidate)
            result["source_freshness_end_attestation"]=final_lock["_freshness_attestation"]
            result["status"]="complete_editorial_review_pending"
    except Exception as exc:
        result["status"]="incomplete_or_error"
        result["error"]=repr(exc)
        print("QUALITY_ABORT",repr(exc),flush=True)
    finally:
        stop(server)
        save_result()
        print("QUALITY_DONE",result["status"],"rows",len(result["rows"]),result_path,flush=True)
    if result["status"]!="complete_editorial_review_pending":raise SystemExit(4)
if __name__=="__main__":main()
