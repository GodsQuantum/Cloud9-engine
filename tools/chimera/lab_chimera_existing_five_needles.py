#!/usr/bin/env python3
"""One-shot GPU LAB smoke of native Cloud9 chimera with official PVE admission.
Acquires the same /run GPU lock as the production router. Never stops services.
Always terminates only its own inference process and writes a report.
"""
import fcntl, json, os, pathlib, socket, subprocess, time, urllib.request, urllib.error
import argparse, importlib.util, hashlib, threading, re
LAB=pathlib.Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/chimera-master9ae-turbo-policy-vulkan-20261024/native-adaptive-vulkan-lab")
GUARD=("192.168.1.200",19755)
parser=argparse.ArgumentParser()
parser.add_argument("--target",type=int,choices=[8192,16384,32768,65536,131072],required=True)
parser.add_argument("--rep-start",type=int,choices=[1,2,3],default=1)
parser.add_argument("--rep-end",type=int,choices=[1,2,3],default=3)
parser.add_argument("--kv-k",choices=["f16","q8_0"],default="f16")
parser.add_argument("--kv-v",choices=["f16","q8_0","turbo3"],default="f16")
parser.add_argument("--batch",type=int,choices=[256,512],default=256)
parser.add_argument("--engine-build",choices=["baseline","nextn-revert"],default="baseline")
parser.add_argument("--trial-id",default="",help="New immutable trial suffix; [A-Za-z0-9_-], max 48 chars")
args_parsed=parser.parse_args()
assert args_parsed.rep_start<=args_parsed.rep_end
if args_parsed.trial_id and not re.fullmatch(r"[A-Za-z0-9_-]{1,48}",args_parsed.trial_id):
    parser.error("trial-id must be 1..48 ASCII alphanumeric, underscore or hyphen")
TARGET=args_parsed.target
if TARGET>=32768 and (args_parsed.kv_k!="q8_0" or args_parsed.kv_v!="q8_0"):
    parser.error("LONG_CTX_32K_PLUS_REQUIRES_Q8_BOTH_KV: CPU/GPU quality requires separate validation")
RUN_SUFFIX="" if (args_parsed.rep_start==1 and args_parsed.rep_end==3) else f"_rep{args_parsed.rep_start}to{args_parsed.rep_end}"
if args_parsed.engine_build!="baseline":
    RUN_SUFFIX+=f"_build_{args_parsed.engine_build.replace('-','_')}"
if args_parsed.kv_k!="f16" or args_parsed.kv_v!="f16" or args_parsed.batch!=256:
    RUN_SUFFIX+=f"_k{args_parsed.kv_k}_v{args_parsed.kv_v}_b{args_parsed.batch}"
if args_parsed.kv_v=="turbo3":
    RUN_SUFFIX+="_blocked_policy"  # Keep original failed quality evidence immutable
if args_parsed.trial_id:
    RUN_SUFFIX+=f"_trial_{args_parsed.trial_id}"
# The historic 8K fixture contains ~8,015 tokenizer tokens. Allocate
# target + 512 for chat formatting and answer, not an unnecessary 12K/22K KV.
CONTEXT = TARGET + 512
RESERVE = {8192:5.4,16384:6.2,32768:7.0,65536:7.8,131072:9.0}[TARGET]
# LAB headroom stricter than the authoritative GPU guard; prior 8K launch
# lost memory/PSI headroom after loading. Never reduce official thresholds.
LAB_START_MEM_GIB = {8192:27.0,16384:30.0,32768:26.2,65536:27.5,131072:29.0}[TARGET]
LAB_START_MAX_SWAP_PCT = 95.0
LAB_START_MAX_PSI_FULL = 0.35
def lab_start_preflight(state):
    # Official PVE guardian must still grant CHECK coexist-light reserve before
    # reaching this stricter LAB-only check. Normal mode uses 27 GiB at 8K.
    stable=(state.get("swap_used_percent",100)<LAB_START_MAX_SWAP_PCT and
            state.get("psi_memory_full_avg10",99)<LAB_START_MAX_PSI_FULL)
    if not stable: return False
    if state.get("mem_available_gib",0)>=LAB_START_MEM_GIB: return True
    # Native ZRAM2 coexistence fallback is LAB-only, without relaxing the
    # authoritative GPU guardian, emergency watchdog or 20/21 GiB runtime floor.
    zram2=pathlib.Path("/sys/block/zram2")
    try:
        resident_ready=(int((zram2/"disksize").read_text())>=4*1024**3 and
                        (zram2/"initstate").read_text().strip()=="1")
    except (OSError, ValueError):
        return False
    if not resident_ready or state.get("swap_total_gib",0)<23:
        return False
    if TARGET==8192:
        return (state.get("swap_used_percent",100)<83.0 and
                state.get("mem_available_gib",0)>=24.6 and
                state.get("psi_memory_full_avg10",99)<0.10 and
                state.get("safe_total_gtt_gib",0)>=7.2)
    # 16K: stricter than 8K; 6.2 GiB pre-admission already mandatory and
    # a guarded failure must not be retried on the same immutable trial ID.
    if TARGET==16384:
        return (state.get("swap_used_percent",100)<78.0 and
                state.get("mem_available_gib",0)>=25.3 and
                state.get("psi_memory_full_avg10",99)<0.05 and
                state.get("safe_total_gtt_gib",0)>=7.8)
    # For 32K/64K/128K there is deliberately NO zram2 reduced-floor
    # fallback: this unqualified long-context path requires full headroom.
    return False
WATCH_STOP=threading.Event()
WATCH_EVENTS=[]
OUT={"engine":"Cloud9-native-chimera-master9ae-r120-mmb-mtp-turbo-adaptive-vulkan-guardian","backend":"Vulkan","model":"Qwen3.8-4B-Heretic MTP Q4_K_M","lab_only":True,"production_promoted":False,"status":"not_started","target_tokens":TARGET,
     "kv_k":args_parsed.kv_k,"kv_v":args_parsed.kv_v,"batch":args_parsed.batch,
     "experimental_cache_quality_test":args_parsed.kv_v!="f16",
     "binary_variant":args_parsed.engine_build}

LOG=LAB/f"chimera_five_needles_{TARGET}_efficient_ctx_cooldown{RUN_SUFFIX}.log"
REPORT=LAB/f"chimera_five_needles_{TARGET}_efficient_ctx_cooldown{RUN_SUFFIX}.json"
if LOG.exists() or REPORT.exists():
    parser.error("REFUSE_TO_OVERWRITE_EVIDENCE: existing run path; supply a unique --trial-id (no replay)")
BINARY=(LAB/"bin/llama-server" if args_parsed.engine_build=="baseline" else
        LAB.parent/"chimera-master9ae-nextn-revert-vulkan-20261025/bin/llama-server")
EXPECTED_SERVER_SHA256={
    "baseline":"2e00292ca25dd5f7e7483f232d2b0c7fe30ba73deea503dcdb4792ac36e47cc3",
    "nextn-revert":"25e2d4560ecceeda57a9c6fa88bfd8b440c46f5bac5dfc71204002a1f798ed63",
}

WEIGHTS=pathlib.Path("/srv/lxc/ia-compute/data/models/bakeoff-20261002/qwen38distill-qwen35-4b-mtp/Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf")
BASE="http://127.0.0.1:18127"
def check(req=None):
    if req is None: req=RESERVE
    with socket.create_connection(GUARD,timeout=4) as s:
        s.settimeout(4)
        s.sendall(f"CHECK coexist-light {req:.2f}\n".encode())
        return json.loads(s.recv(16384).decode())
def json_url(url,body=None,timeout=2):
    data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None
    r=urllib.request.Request(url,data=data,headers={"Content-Type":"application/json"} if data else {})
    with urllib.request.urlopen(r,timeout=timeout) as f:return json.load(f)
def docker_id(name):
    return subprocess.check_output(["docker","inspect","-f","{{.Id}}",name],text=True,timeout=7).strip()
def rendering_unknown():
    target=os.path.realpath("/dev/dri/renderD128")
    ids=[docker_id(x) for x in ("voicestudio","autosubs-aligner-gpu","speaches")]
    unknown=[]
    for f in os.listdir("/proc"):
        if not f.isdigit():continue
        path=f"/proc/{f}"
        try:
            if not any(os.path.realpath(path+"/fd/"+fd)==target for fd in os.listdir(path+"/fd")):continue
            group=pathlib.Path(path+"/cgroup").read_text()
            if "cloud9-embedding.service" in group or any(x in group for x in ids):continue
            unknown.append(f)
        except (FileNotFoundError,OSError,PermissionError):pass
    return unknown
def running_clients(port):
    proc=subprocess.run(["ss","-Htn","state","established","sport","=",f":{port}"],capture_output=True,text=True,timeout=3)
    return proc.returncode!=0 or bool(proc.stdout.strip())
def guarded_safe():
    if json_url("http://192.168.1.219:8090/health",timeout=3).get("worker_model") is not None:
        raise RuntimeError("Production router has an active generation worker")
    for port in (3900,7443,8007):
        if running_clients(port):raise RuntimeError(f"Existing GPU client on port {port}")
    a=json_url("http://192.168.1.219:8007/health",timeout=3)
    if a.get("status")!="ok" or a.get("loaded_models")!=[]:
        raise RuntimeError("AutoSubs Aligner not idle")
    u=rendering_unknown()
    if u:raise RuntimeError(f"Unknown GPU render device consumers: {u}")
def run():
    assert BINARY.is_file() and WEIGHTS.is_file()
    actual_sha=hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert actual_sha==EXPECTED_SERVER_SHA256[args_parsed.engine_build], "LAB_BINARY_SHA256_CHANGED"
    OUT["binary_sha256"]=actual_sha
    if args_parsed.kv_v=="turbo3":
        # Negative real Vulkan quality result 25 Oct 2026 (8K: 5/5
        # exact-retrieval FAILED, per-marker count unknown; 3.51 tok/s).
        # Do not replay a known failed kernel/quant build.
        OUT["status"]="blocked_known_bad_turbo3_quality"
        OUT["reason"]="PROVEN_BAD_VULKAN_TURBO3_8K_20261025"
        return
    OUT["gguf_bytes"]=WEIGHTS.stat().st_size
    guarded_safe()
    state=check(RESERVE)
    OUT["admission"]={k:state.get(k) for k in ("allow","mem_available_gib","psi_memory_full_avg10","safe_total_gtt_gib","swap_used_percent","reasons")}
    if not state.get("allow"):
        OUT["status"]="blocked_guardian";return
    if not lab_start_preflight(state):
        OUT["status"]="blocked_lab_memory_headroom"
        OUT["lab_headroom_limits"]={"min_mem_gib":LAB_START_MEM_GIB,"max_swap_pct":LAB_START_MAX_SWAP_PCT,"max_psi_full_avg10":LAB_START_MAX_PSI_FULL}
        return
    fd=os.open("/run/cloud9-gpu.lock",os.O_RDWR|os.O_CREAT,0o660)
    proc=None
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            OUT["status"]="gpu_lock_busy";return
        guarded_safe()
        state=check(RESERVE)
        if not state.get("allow"):
            OUT["status"]="blocked_guardian_after_lock";OUT["guard_after_lock"]=state;return
        if not lab_start_preflight(state):
            OUT["status"]="blocked_lab_headroom_after_lock"
            OUT["guard_after_lock"]=state
            return
        if args_parsed.kv_v!="f16" and state.get("swap_used_percent",100)>95:
            OUT["status"]="blocked_experimental_kv_swap_safety"
            OUT["guard_after_lock"]=state
            return
        # ELF loader uses native $ORIGIN RUNPATH in the LAB binary, not a wrapper
        # or a global LD_LIBRARY_PATH override that could affect other engines.
        env=os.environ.copy()
        # Match production Cloud9 router's RADV driver mode for A/B isolation.
        perf=[x for x in env.get("RADV_PERFTEST","").split(",") if x]
        if "nogttspill" not in perf:perf.append("nogttspill")
        env["RADV_PERFTEST"]=",".join(perf)
        OUT["driver_flag"]=env["RADV_PERFTEST"]
        args=[str(BINARY),"-m",str(WEIGHTS),"-ngl","99","-c",str(CONTEXT),"-np","1",
              "-b",str(args_parsed.batch),"-ub",str(args_parsed.batch),"-t","6","-tb","6","-fa","on",
              "-ctk",args_parsed.kv_k,"-ctv",args_parsed.kv_v,"--fit","off","--host","127.0.0.1","--port","18127",
              "--no-context-shift","-lm","mmap","--poll","100","--poll-batch","0","--lazy-mode","off",
              "--no-warmup","--no-webui","--alias","Cloud9-Chimera-Qwen4-LAB",
              "--jinja","--reasoning","off","--reasoning-budget","0",
              "--spec-type","draft-mtp","--spec-draft-n-max","2","--spec-draft-p-min","0"]
        OUT["args_public"]=[x if x!=str(WEIGHTS) else WEIGHTS.name for x in args]
        with LOG.open("w") as logfile:
            start=time.monotonic()
            proc=subprocess.Popen(args,stdout=logfile,stderr=subprocess.STDOUT,env=env)
            ready=False
            for i in range(130):
                if proc.poll() is not None:break
                try:
                    h=json_url(BASE+"/health",timeout=1)
                    if h.get("status")=="ok":ready=True;break
                except (OSError,urllib.error.URLError):pass
                if i%12==11:
                    g=check(0)
                    if g.get("psi_memory_full_avg10",0)>=4 or g.get("mem_available_gib",0)<18:break
                time.sleep(.5)
            OUT["load_seconds"]=round(time.monotonic()-start,2)
            if not ready:
                OUT["status"]="startup_failed_or_pressure_abort"
                OUT["exit_code"]=proc.poll();return
            # Reuse the SAME deterministic five-marker fixture generator as
            # the historical Atomic TurboQuant 8K/16K certified tests.
            source=LAB/"atomic_turboquant_context_20261022.py"
            spec=importlib.util.spec_from_file_location("historical_five_needles",source)
            fixture=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fixture)
            fixture.api=lambda endpoint,body=None,seconds=120:json_url(BASE+endpoint,body,timeout=seconds)
            count, text=fixture.build_target(TARGET)
            OUT["status"]="fixture_ready"
            OUT["fixture_sha256"]=hashlib.sha256(text.encode()).hexdigest()
            OUT["measured_tokenizer_tokens"]=count
            OUT["ctx_allocated"]=CONTEXT
            OUT["repetitions_planned"]=args_parsed.rep_end-args_parsed.rep_start+1
            OUT["expected"]=fixture.CODES
            OUT["rows"]=[]
            def stop_own_lab_child():
                # Only this Popen handle can be stopped; do not touch the
                # production route, native embeddings, voice, or PVE guests.
                if proc.poll() is not None: return
                proc.terminate()
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=7)
            def watch():
                while not WATCH_STOP.wait(2):
                    try:
                        state=check(0)
                        if (state.get("psi_memory_full_avg10",99)>2.0 or
                            state.get("mem_available_gib",0)<19.0):
                            WATCH_EVENTS.append({"reason":"HOST_MEMORY_PSI","guard":state})
                        for temp in pathlib.Path("/sys/class/hwmon").glob("hwmon*/name"):
                            if temp.read_text().strip()=="k10temp":
                                v=int((temp.parent/"temp1_input").read_text())/1000
                                if v>=79.0:WATCH_EVENTS.append({"reason":"CPU_TCTL","value":v})
                        if WATCH_EVENTS:
                            stop_own_lab_child()
                            break
                    except Exception as e:
                        WATCH_EVENTS.append({"reason":"WATCHDOG_UNAVAILABLE","error":str(e)[:100]})
                        stop_own_lab_child()
                        break
            thread=threading.Thread(target=watch,daemon=True)
            thread.start()
            try:
                # CHECK 5.4 GiB was already enforced TWICE BEFORE admission and
                # taking the GPU lock. The 24-GiB floor is an admission
                # threshold, not a post-allocation requirement: requiring it
                # after allocating the admitted 8K worker makes every launch
                # spuriously fail. Still enforce a 20-GiB emergency runtime
                # floor and no persistent memory stalls. Wait for transient
                # model-loader PSI to settle; never bypass initial admission.
                stable=0
                for _ in range(15):
                    g=check(0)
                    if WATCH_EVENTS or g.get("mem_available_gib",0)<20.0 or g.get("psi_memory_full_avg10",99)>=2.0:
                        OUT["status"]="stopped_after_load_safety"
                        OUT["guard_after_load"]=g
                        break
                    if g.get("psi_memory_full_avg10",99)<0.5 and g.get("mem_available_gib",0)>=21.0:
                        stable+=1
                        if stable>=2:break
                    else:stable=0
                    time.sleep(2)
                if stable<2:
                    OUT["status"]=OUT.get("status") if OUT.get("status")=="stopped_after_load_safety" else "stopped_after_load_unstable"
                    OUT["guard_after_load"]=g
                    return
                OUT["postload_stability_verified"]=True
                for rep in range(args_parsed.rep_start,args_parsed.rep_end+1):
                    # 8K prefill briefly raises PSI; do not discard the loaded
                    # worker just because the 10-s average has not yet decayed.
                    # Runtime survival floor is not new-model admission floor.
                    # Preserve strict fail-closed rules for sustained pressure.
                    stable=0
                    start_stability=time.monotonic()
                    while time.monotonic()-start_stability<55:
                        g=check(0)
                        if WATCH_EVENTS or g.get("mem_available_gib",0)<20.0 or g.get("psi_memory_full_avg10",99)>=2.0:
                            break
                        if g.get("psi_memory_full_avg10",99)<0.5 and g.get("mem_available_gib",0)>=21.0:
                            stable+=1
                            if stable>=2:break
                        else:
                            stable=0
                        time.sleep(2)
                    if stable<2 or WATCH_EVENTS:
                        OUT["status"]="stopped_for_memory_pressure"
                        OUT["guard_before_rep"]=g
                        OUT["pressure_wait_seconds"]=round(time.monotonic()-start_stability,2)
                        break
                    body={"model":"Cloud9-Chimera-Qwen4-LAB",
                          "messages":[{"role":"user","content":text}],
                          "seed":42+rep,"temperature":0,"max_tokens":160,"stream":False,
                          "enable_thinking":False,"cache_prompt":False}
                    started=time.monotonic()
                    try:
                        answer=json_url(BASE+"/v1/chat/completions",body,timeout=max(230,round(TARGET/250*1.7)))
                    except Exception as ex:
                        OUT["status"]="inference_failed_or_watchdog"
                        OUT["request_error"]=type(ex).__name__+": "+str(ex)[:250]
                        break
                    use=answer.get("usage") or {}
                    msg=((answer.get("choices") or [{}])[0].get("message") or {})
                    content=(msg.get("content") or "").strip()
                    try:parsed=json.loads(content)
                    except (ValueError,TypeError):parsed=None
                    full=use.get("prompt_tokens",0)>=TARGET*.9
                    row={"rep":rep,"prompt_tokens":use.get("prompt_tokens"),
                         "five_correct":parsed==fixture.CODES,"full_prompt_ingested":full,
                         "wall_s":round(time.monotonic()-started,3),
                         "decode_tps":(answer.get("timings") or {}).get("predicted_per_second"),
                         "prefill_tps":(answer.get("timings") or {}).get("prompt_per_second"),
                         "answer_sha256":hashlib.sha256(content.encode()).hexdigest(),
                         "watchdog_events":len(WATCH_EVENTS)}
                    OUT["rows"].append(row)
                    REPORT.write_text(json.dumps(OUT,ensure_ascii=False,indent=2)+"\n")
                    print("FIVE_NEEDLES_REAL_CASE",json.dumps(row,ensure_ascii=False),flush=True)
                    if not full or not row["five_correct"] or WATCH_EVENTS:
                        OUT["status"]="quality_failure_or_watchdog"
                        break
                else:
                    OUT["status"]="complete"
            finally:
                WATCH_STOP.set()
                thread.join(timeout=3)
                OUT["watchdog_events"]=WATCH_EVENTS
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=12)
            except subprocess.TimeoutExpired:
                proc.kill();proc.wait(timeout=5)
        fcntl.flock(fd,fcntl.LOCK_UN)
        os.close(fd)
try:run()
except Exception as e:
    OUT["status"]="error";OUT["error"]=type(e).__name__+": "+str(e)[:430]
finally:
    if LOG.is_file():
        OUT["log_tail"]=LOG.read_text(errors="replace")[-2800:]
    REPORT.write_text(json.dumps(OUT,ensure_ascii=False,indent=2)+"\n")
    print("CHIMERA_LAB_RESULT",json.dumps({k:OUT.get(k) for k in ("status","load_seconds","request_s","timings","usage","answer","error","log_tail")},ensure_ascii=False),flush=True)
