#!/usr/bin/env python3
"""Guarded Flash-Next Strata real-GPU smoke on Cloud9 (host-only).

NO restarts, mount changes, credential access or changes to production runtime.
Uses CT410 official admission + GPU lock and fail-closed host watchdog. All paths
are controlled, model data read-only. Never reports a speed without generation.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import time

ROOT=Path("/srv/storage/nvme/DEV/Projets/HomeLab/Moteurs IA")
MODEL=Path("/srv/lxc/ia-compute/data/models/strata")
ARCH=ROOT/"Sources/Archive/CT410_DEV_REPATRIATION_20261017/strata-runtime"
BINARY=ROOT/"Sources/Builds/strata-v022-gfx1103-codespace-hip/strata"
OUT=ROOT/"Sources/Worklogs/2026-10-22_STRATA_FLASHNEXT_CODER_V0147_GUARDED_REALGPU_V4.log"
LIMIT=7.0
def command(args,timeout=12):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if p.returncode:raise RuntimeError(f"{args[0]} failed rc{p.returncode}: {p.stderr[-160:]}")
    return p.stdout
def metrics():
    mem=Path("/proc/meminfo").read_text()
    ks={k:int(v) for k,v in re.findall(r"^(MemAvailable|SwapTotal|SwapFree):\s+(\d+)",mem,re.M)}
    t=re.search(r"Tctl:\s+\+([\d.]+)",command(["sensors"],5))
    p=re.search(r"^full avg10=([\d.]+)",Path("/proc/pressure/memory").read_text(),re.M)
    if not t or not p:raise RuntimeError("critical hardware sensor missing")
    return {"mem_gib":ks["MemAvailable"]/1048576,
      "psi_full10":float(p.group(1)),"temp_c":float(t.group(1)),
      "swap_used_pct":100*(ks["SwapTotal"]-ks["SwapFree"])/max(ks["SwapTotal"],1),
      "gtt_gib":int(Path("/sys/class/drm/card0/device/mem_info_gtt_used").read_text())/1073741824}
def gpu_users():
    p=command(["/usr/sbin/pct","exec","410","--","ss","-Htn","state","established"],7)
    return bool(re.search(r":(?:8005|8007|8010|3900|7443|8090|18091)\b",p))
def admission():
    code='import socket;s=socket.create_connection(("192.168.1.200",19755),3);s.sendall(b"CHECK coexist-light 5.0\\n");print(s.recv(8192).decode());s.close()'
    return json.loads(command(["/usr/sbin/pct","exec","410","--","python3","-c",code],10))
def owned_cmdline(binary,args):
    return [str(binary)]+args
def runner_arguments(args):
    shards=sorted((MODEL/"coder-iq1m").glob("Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-*.gguf"))
    if len(shards)!=2 or sum(p.stat().st_size for p in shards)!=58408584928:
        raise ValueError("model shards missing or wrong size")
    pack=MODEL/"packs/coder-iq1m"
    mtp=ARCH/"mtp-qwen38/rt"
    for p in [BINARY,pack/"dense.bin",mtp]:
        if not p.exists():raise ValueError(f"runtime asset missing: {p}")
    arg=["--pack",str(pack),"--native",str(shards[0]),"--ple-gguf",str(shards[1]),
       "--ple-io","direct","--mmap-experts","--expert-cache","320",
       "--expert-cache-per-layer","--mtp",str(mtp),"--spec","4",
       "--spec-min-p","0.5","--suffix-draft","0","--prefill","512","--max-context","4096",
       "--kv","int8","--pool-workers","6","--adapt-every","0","--pcie-frac","0",
       "--vram-reserve-mib","2048","--tokens","1,2,3","--max-new",str(args.max_new),"--stats"]
    return owned_cmdline(BINARY,arg)
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--max-new",type=int,default=16)
    a.add_argument("--duration",type=int,default=240)
    args=a.parse_args()
    if not 1<=args.max_new<=64 or not 15<=args.duration<=360:raise ValueError("bounds")
    run=runner_arguments(args)
    sdk=ARCH/"rocm-gfx1103/lib/python3.14/site-packages"
    env={**os.environ,"LD_LIBRARY_PATH":":".join(str(sdk/p) for p in [
        "_rocm_sdk_devel/lib","_rocm_sdk_libraries/lib","_rocm_sdk_core/lib"]),
        "STRATA_DEVICE_BUDGET_MIB":"6144","STRATA_ARENA_PIN_GIB":"0",
        "STRATA_RESIDENT_HEADROOM_GIB":"20","HIP_VISIBLE_DEVICES":"0",
        "OMP_NUM_THREADS":"6"}
    lease=proc=None
    with OUT.open("x",encoding="utf-8",buffering=1) as file:
        os.chown(OUT,1000,1000)
        def say(v):
            line=str(v)
            print(line,flush=True)
            file.write(line+"\n")
        try:
            say("PRECHECK "+json.dumps(metrics()))
            ok=False
            for i in range(18):
                m=metrics()
                if m["mem_gib"]>=24 and m["psi_full10"]<.35 and m["temp_c"]<74 and m["gtt_gib"]<2.5 and not gpu_users():
                    g=admission()
                    if g.get("allow") and g.get("safe_total_gtt_gib",0)>=5:
                        say("OFFICIAL_CT410_ALLOW "+json.dumps(g))
                        ok=True
                        break
                time.sleep(5)
            if not ok:raise RuntimeError("CT410 official resource admission refused")
            gspec=importlib.util.spec_from_file_location("gpu_guard",str(ROOT/"Sources/Tools/cloud9_vulkan_coexist_bench_guard_20261017.py"))
            guard=importlib.util.module_from_spec(gspec)
            gspec.loader.exec_module(guard)
            guard.classify_users()
            lease=subprocess.Popen(["/usr/sbin/pct","exec","410","--","flock","-n","/run/cloud9-gpu.lock",
                 "bash","-lc","echo LOCK_GRANTED; read -r _"],
                 stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            ready,_,_=select.select([lease.stdout],[],[],12)
            if not ready or lease.stdout.readline().strip()!="LOCK_GRANTED":
                raise RuntimeError("GPU lease unavailable")
            if gpu_users():raise RuntimeError("GPU production client raced lease")
            say("GPU_EXCLUSIVE_LOCK")
            say("COMMAND "+json.dumps(run))
            proc=subprocess.Popen(run,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
                start_new_session=True,env=env,bufsize=1)
            begun=time.monotonic();last=0;pressure_since=None;abort=None
            min_avail=999;peak_gtt=peak_temp=0
            while proc.poll() is None:
                rd,_,_=select.select([proc.stdout],[],[],1)
                if rd:
                    line=proc.stdout.readline()
                    if line:say(line.rstrip())
                if time.monotonic()-last<2:continue
                last=time.monotonic()
                m=metrics()
                min_avail=min(min_avail,m["mem_gib"])
                peak_gtt=max(peak_gtt,m["gtt_gib"])
                peak_temp=max(peak_temp,m["temp_c"])
                if m["psi_full10"]>=1.4:
                    if pressure_since is None:pressure_since=last
                else:pressure_since=None
                if m["mem_gib"]<18.6 or m["temp_c"]>=78 or m["gtt_gib"]>LIMIT or m["swap_used_pct"]>=93:
                    abort="HARD_SAFETY "+json.dumps(m)
                elif m["psi_full10"]>=5 or (m["psi_full10"]>=2 and m["mem_gib"]<24):
                    abort="CRITICAL_MEMORY_PSI "+json.dumps(m)
                elif pressure_since is not None and last-pressure_since>=20:
                    abort="SUSTAINED_MEMORY_PSI "+json.dumps(m)
                elif gpu_users():abort="PRODUCTION_GPU_CLIENT"
                elif lease.poll() is not None:abort="GPU_LEASE_LOST"
                elif last-begun>=args.duration:abort="SMOKE_DURATION_LIMIT"
                if abort:
                    say("FAIL_CLOSED "+abort)
                    os.killpg(proc.pid,signal.SIGTERM)
                    break
            if proc.poll() is None:
                try:proc.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL)
                    proc.wait(timeout=9)
            for line in proc.stdout:say(line.rstrip())
            say("FINAL "+json.dumps({"exit":proc.returncode,"aborted":abort,
              "wall_s":round(time.monotonic()-begun,3),"min_host_mem_gib":min_avail,
              "peak_gtt_gib":peak_gtt,"peak_Tctl_C":peak_temp}))
            if proc.returncode or abort:raise RuntimeError("Strata candidate NOT certified")
        finally:
            if proc and proc.poll() is None:
                os.killpg(proc.pid,signal.SIGTERM)
                try:proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL)
                    proc.wait(timeout=10)
            if lease and lease.poll() is None:
                try:lease.stdin.write("release\n");lease.stdin.flush();lease.wait(timeout=8)
                except Exception:lease.terminate()
            say("GPU_LOCK_RELEASED")
if __name__=="__main__":main()
