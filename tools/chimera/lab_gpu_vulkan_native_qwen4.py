#!/usr/bin/env python3
"""One-shot GPU LAB smoke of native Cloud9 chimera with official PVE admission.
Acquires the same /run GPU lock as the production router. Never stops services.
Always terminates only its own inference process and writes a report.
"""
import fcntl, json, os, pathlib, socket, subprocess, time, urllib.request, urllib.error
LAB=pathlib.Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/chimera-master9ae-turbo-policy-vulkan-20261024/native-adaptive-vulkan-lab")
LOG=LAB/"chimera_qwen4_first_real_gpu.log"
REPORT=LAB/"chimera_qwen4_first_real_gpu.json"
BINARY=LAB/"bin/llama-server"
WEIGHTS=pathlib.Path("/srv/lxc/ia-compute/data/models/bakeoff-20261002/qwen38distill-qwen35-4b-mtp/Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf")
BASE="http://127.0.0.1:18127"
GUARD=("192.168.1.200",19755)
OUT={"engine":"Cloud9-native-chimera-master9ae-r120-mmb-mtp-turbo-adaptive-vulkan-guardian","backend":"Vulkan","model":"Qwen3.8-4B-Heretic MTP Q4_K_M","lab_only":True,"production_promoted":False,"status":"not_started"}
def check(req=4.1):
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
    OUT["gguf_bytes"]=WEIGHTS.stat().st_size
    guarded_safe()
    state=check()
    OUT["admission"]={k:state.get(k) for k in ("allow","mem_available_gib","psi_memory_full_avg10","safe_total_gtt_gib","swap_used_percent","reasons")}
    if not state.get("allow"):
        OUT["status"]="blocked_guardian";return
    fd=os.open("/run/cloud9-gpu.lock",os.O_RDWR|os.O_CREAT,0o660)
    proc=None
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            OUT["status"]="gpu_lock_busy";return
        guarded_safe()
        state=check()
        if not state.get("allow"):
            OUT["status"]="blocked_guardian_after_lock";OUT["guard_after_lock"]=state;return
        # ELF loader uses native $ORIGIN RUNPATH in the LAB binary, not a wrapper
        # or a global LD_LIBRARY_PATH override that could affect other engines.
        env=os.environ.copy()
        # Match production Cloud9 router's RADV driver mode for A/B isolation.
        perf=[x for x in env.get("RADV_PERFTEST","").split(",") if x]
        if "nogttspill" not in perf:perf.append("nogttspill")
        env["RADV_PERFTEST"]=",".join(perf)
        OUT["driver_flag"]=env["RADV_PERFTEST"]
        args=[str(BINARY),"-m",str(WEIGHTS),"-ngl","99","-c","2048","-np","1",
              "-b","256","-ub","256","-t","6","-tb","6","-fa","on",
              "-ctk","f16","-ctv","f16","--fit","off","--host","127.0.0.1","--port","18127",
              "-lm","mmap","--poll","100","--poll-batch","0","--lazy-mode","off",
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
            payload={"model":"Cloud9-Chimera-Qwen4-LAB",
                "messages":[{"role":"user","content":"Réponds en français en 3 points très courts : comment garder Proxmox fiable pendant un test LLM GPU ?"}],
                "temperature":0.2,"max_tokens":175,"stream":False}
            g=check(0)
            if g.get("psi_memory_full_avg10",0)>=1 or g.get("mem_available_gib",0)<20:
                OUT["status"]="loaded_but_high_pressure_skip_inference";OUT["load_guard"]=g;return
            t=time.monotonic()
            try:
                ans=json_url(BASE+"/v1/chat/completions",payload,timeout=95)
                choice=(ans.get("choices") or [{}])[0]
                msg=choice.get("message") or {}
                content=msg.get("content") or ""
                OUT.update({"status":"complete" if content.strip() else "empty_answer","request_s":round(time.monotonic()-t,2),
                    "usage":ans.get("usage"),"timings":ans.get("timings"),"message":msg,
                    "finish_reason":choice.get("finish_reason"),"answer":content[:1500]})
                # One simulated agentic read-only tool call, no execution.
                if OUT["status"]=="complete":
                    import importlib.util
                    bpath=pathlib.Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/local-agent-readiness-20261024")
                    spec=importlib.util.spec_from_file_location("agentbench",bpath/"bench_native_agent_tools.py")
                    agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)
                    f=agent.fixture_list(bpath/"infra_agentic_fixtures.json")[0]
                    request={"model":"Cloud9-Chimera-Qwen4-LAB","temperature":0,"stream":False,
                        "tool_choice":"required","parallel_tool_calls":False,"max_tokens":125,
                        "messages":[{"role":"system","content":"Choisis exactement un outil en lecture seule; aucune intervention."},
                            {"role":"user","content":f["prompt_fr"]}],
                        "tools":agent.toolbox(f)}
                    try:
                        reply=json_url(BASE+"/v1/chat/completions",request,timeout=65)
                        grade=agent.score(reply,f)
                        grade["usage"]=reply.get("usage")
                        grade["timings"]=reply.get("timings")
                        grade["calls"]=((reply.get("choices") or [{}])[0].get("message") or {}).get("tool_calls")
                        OUT["agentic"]=grade
                    except Exception as e:
                        OUT["agentic"]={"passed":False,"error":type(e).__name__+": "+str(e)[:150]}
            except Exception as e:
                OUT["status"]="request_failed";OUT["error"]=type(e).__name__+": "+str(e)[:300]
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
