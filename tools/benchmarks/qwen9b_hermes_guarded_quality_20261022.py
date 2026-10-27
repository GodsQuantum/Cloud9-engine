#!/usr/bin/env python3
"""Guarded 9B MTP agentic test on Cloud9; no service/VM changes.

Requires official CT410 admission + exclusive lease + live RAM/PSI/GTT/Tctl.
The model and GPU worker run in DEV CT700 as UID 1000, never on the host.
"""
import json,os,re,select,signal,subprocess,time,importlib.util
from pathlib import Path

ROOT=Path("/srv/storage/nvme/DEV/Projets/HomeLab/Moteurs IA")
LOG=ROOT/"Sources/Worklogs/2026-10-22_QWEN9B_HERMES_FC_MTP2_QUALITY36_GUARDED_V2_RESUME.log"
ARC=Path("/sys/module/zfs/parameters/zfs_arc_max")
BENCH="/home/arezki/Projets/HomeLab/Moteurs IA/Sources/Scratch/cloud9-engine-qualification-20261022-host/tools/benchmarks/live_quality12_mtp_20261022.py"
MODEL="qwen3.8-9b-hermes-fc-tooluse.Q4_K_M.gguf"
def run(args,timeout=10):
    r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if r.returncode:raise RuntimeError(f"{args[0]} rc={r.returncode} {r.stderr[-200:]}")
    return r.stdout
def monitor():
    raw=Path("/proc/meminfo").read_text()
    d={k:int(v) for k,v in re.findall(r"^(MemAvailable|SwapTotal|SwapFree):\s+(\d+)",raw,re.M)}
    psi=float(re.search(r"^full avg10=([\d.]+)",Path("/proc/pressure/memory").read_text(),re.M).group(1))
    t=re.search(r"Tctl:\s+\+([\d.]+)",run(["sensors"],5))
    if not t:raise RuntimeError("Missing thermal sensor")
    return {"mem":d["MemAvailable"]/1048576,"psi":psi,"temp":float(t.group(1)),
        "swap":100*(d["SwapTotal"]-d["SwapFree"])/max(d["SwapTotal"],1),
        "gtt":int(Path("/sys/class/drm/card0/device/mem_info_gtt_used").read_text())/1073741824}
def arbiter():
    code='import socket;s=socket.create_connection(("192.168.1.200",19755),3);s.sendall(b"CHECK coexist-light 8.0\\n");print(s.recv(8192).decode());s.close()'
    return json.loads(run(["/usr/sbin/pct","exec","410","--","python3","-c",code],9))
def clients():
    s=run(["/usr/sbin/pct","exec","410","--","ss","-Htn","state","established"],7)
    return bool(re.search(r":(?:8005|8007|8010|3900|7443|8090|18091)\b",s))
def cleanup():
    py=r'''from pathlib import Path
import os,signal
for x in Path("/proc").iterdir():
 if not x.name.isdecimal():continue
 try:
  line=(x/"cmdline").read_bytes().replace(b"\0",b" ").decode(errors="replace")
  if "/llama-b11798-codespace-20261022/bin/llama-server" in line and "--port 18229" in line and "qwen3.8-9b-hermes-fc-tooluse.Q4_K_M.gguf" in line:
   os.kill(int(x.name),signal.SIGTERM)
   print("SCOPED_WORKER_TERMINATED",x.name)
 except (OSError,PermissionError):pass'''
    r=subprocess.run(["/usr/sbin/pct","exec","700","--","python3","-c",py],capture_output=True,text=True,timeout=12)
    return r.stdout.strip()
def main():
    old=int(ARC.read_text())
    lease=worker=None
    with LOG.open("x",encoding="utf8",buffering=1) as f:
        os.chown(LOG,1000,1000)
        def say(s):
            s=str(s)
            print(s,flush=True)
            f.write(s+"\n")
        try:
            say("START "+json.dumps(monitor()))
            if old>5368709120:
                ARC.write_text("5368709120")
                say("ARC_TEMP_MAX 5368709120")
            accepted=None
            for i in range(26):
                m=monitor()
                if m["mem"]>=24 and m["psi"]<.35 and m["temp"]<74 and m["gtt"]<3 and m["swap"]<90 and not clients():
                    check=arbiter()
                    if check.get("allow") and check.get("safe_total_gtt_gib",0)>=8:
                        accepted=check
                        break
                time.sleep(4)
            if accepted is None:raise RuntimeError("OFFICIAL_CT410_ADMISSION_REFUSED")
            say("OFFICIAL_CT410_ALLOW "+json.dumps(accepted))
            mod=importlib.util.spec_from_file_location("gpu_guard",str(ROOT/"Sources/Tools/cloud9_vulkan_coexist_bench_guard_20261017.py"))
            guard=importlib.util.module_from_spec(mod)
            mod.loader.exec_module(guard)
            guard.classify_users()
            lease=subprocess.Popen(["/usr/sbin/pct","exec","410","--","flock","-n","/run/cloud9-gpu.lock","bash","-lc","echo GPU_LEASE_GRANTED; read -r _"],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            rd,_,_=select.select([lease.stdout],[],[],12)
            if not rd or lease.stdout.readline().strip()!="GPU_LEASE_GRANTED":
                raise RuntimeError("GPU_LOCK_BUSY")
            if clients():raise RuntimeError("PRODUCTION_GPU_CLIENT_RACE")
            say("GPU_LEASE_HELD")
            args=["/usr/sbin/pct","exec","700","--","runuser","-u","arezki","--","env",
                "PYTHONUNBUFFERED=1","CLOUD9_GPU_COEXIST_ADMITTED=1","python3",BENCH,
                "--candidate","b11798-hermes9b","--reps","3","--thermal-pace","--trial-tag","hermes-v1","--resume"]
            worker=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                text=True,bufsize=1,start_new_session=True)
            start=time.monotonic()
            last=0;highpsi=None;abort=None
            peaktemp=peakgtt=0;minmem=999
            while worker.poll() is None:
                ready,_,_=select.select([worker.stdout],[],[],1)
                if ready:
                    line=worker.stdout.readline()
                    if line:say(line.rstrip())
                if time.monotonic()-last<3:continue
                last=time.monotonic();m=monitor()
                minmem=min(minmem,m["mem"]);peaktemp=max(peaktemp,m["temp"]);peakgtt=max(peakgtt,m["gtt"])
                if m["psi"]>=1.4:
                    if highpsi is None:highpsi=last
                else:highpsi=None
                if m["mem"]<18.6 or m["temp"]>=78 or m["gtt"]>9.1 or m["swap"]>=93:
                    abort="HARD_RESOURCE_LIMIT "+json.dumps(m)
                elif m["psi"]>=5 or (m["psi"]>=2 and m["mem"]<24):
                    abort="CRITICAL_PRESSURE "+json.dumps(m)
                elif highpsi is not None and last-highpsi>=21:
                    abort="SUSTAINED_PRESSURE "+json.dumps(m)
                elif lease.poll() is not None:abort="GPU_LEASE_LOST"
                elif clients():abort="PRODUCTION_GPU_CLIENT"
                elif last-start>=780:abort="BENCHMARK_MAX_DURATION"
                if abort:
                    say("FAIL_CLOSED "+abort)
                    os.killpg(worker.pid,signal.SIGTERM)
                    break
            if worker.poll() is None:
                try:worker.wait(timeout=13)
                except subprocess.TimeoutExpired:
                    os.killpg(worker.pid,signal.SIGKILL)
                    worker.wait(timeout=8)
            for line in worker.stdout:say(line.rstrip())
            say("SCOPED_CLEANUP "+cleanup())
            say("FINAL "+json.dumps({"rc":worker.returncode,"aborted":abort,
                "wall":round(time.monotonic()-start,3),
                "peak_temp":peaktemp,"peak_gtt":peakgtt,"minmem":minmem}))
            if abort or worker.returncode:raise RuntimeError("Candidate NOT certified")
        finally:
            if worker and worker.poll() is None:
                os.killpg(worker.pid,signal.SIGTERM)
                try:worker.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(worker.pid,signal.SIGKILL)
                    worker.wait(timeout=9)
            if lease and lease.poll() is None:
                try:
                    lease.stdin.write("release\n");lease.stdin.flush();lease.wait(timeout=8)
                except Exception:lease.terminate()
            ARC.write_text(str(old))
            say("ARC_RESTORED "+ARC.read_text().strip())
            say("GPU_LOCK_RELEASED")
if __name__=="__main__":main()
