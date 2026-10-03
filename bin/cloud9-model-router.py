#!/usr/bin/env python3
import argparse
import fcntl
import http.client
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--host",default="127.0.0.1")
ap.add_argument("--port",type=int,default=18090)
ap.add_argument("--worker-host",default="127.0.0.1")
ap.add_argument("--worker-port",type=int,default=18091)
ap.add_argument("--catalog",default=os.environ.get("CLOUD9_ENGINE_MODEL_CATALOG","/srv/lxc/ia-compute/data/cloud9-engine-runtime/model-catalog.json"))
ap.add_argument("--engine-home",default=os.environ.get("CLOUD9_ENGINE_HOME","/srv/lxc/ia-compute/data/cloud9-engine-runtime"))
ap.add_argument("--idle-seconds",type=int,default=30)
a=ap.parse_args()

ENGINE=Path(a.engine_home)
CATALOG_PATH=Path(a.catalog)
GPU_LOCK=Path("/run/cloud9-gpu.lock")
EMBED_SERVICE="cloud9-embedding.service"
SPEACHES_CONTAINER="speaches"
STATE_DIR=ENGINE/"state"
STATE_DIR.mkdir(parents=True,exist_ok=True)
WORKER_LOG=STATE_DIR/"model-router-worker.log"

def load_catalog():
    data=json.loads(CATALOG_PATH.read_text())
    models=data.get("models",[])
    by={}
    for m in models:
        if not m.get("id") or not m.get("model") or not m.get("backend"):
            raise RuntimeError(f"invalid model catalog entry: {m}")
        by[m["id"]]=m
        by[m["id"].lower()]=m
        for alias in m.get("aliases",[]):
            by[alias]=m; by[alias.lower()]=m
    return data,models,by

catalog,models,model_by_id=load_catalog()

def run_systemctl(*args,check=False,timeout=45):
    p=subprocess.run(["systemctl",*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f"systemctl {' '.join(args)} failed: {p.stderr.strip()}")
    return p

def service_active(name):
    return run_systemctl("is-active","--quiet",name).returncode==0

def run_docker(*args,check=False,timeout=45):
    p=subprocess.run(["docker",*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f"docker {' '.join(args)} failed: {p.stderr.strip()}")
    return p

def container_running(name):
    p=run_docker("inspect","-f","{{.State.Running}}",name,timeout=10)
    return p.returncode==0 and p.stdout.strip().lower()=="true"

def tcp_port_busy(port):
    try:
        p=subprocess.run(
            ["ss","-Htn","state","established","sport","=",f":{port}"],
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=2,
        )
        return p.returncode==0 and bool(p.stdout.strip())
    except Exception:
        return False

def embedding_busy():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8091/slots",timeout=1) as r:
            raw=r.read().decode("utf-8","replace")
        data=json.loads(raw)
        if isinstance(data,list):
            for x in data:
                if x.get("is_processing") is True or x.get("state")=="processing":
                    return True
        return False
    except Exception:
        return False

def gpu_users():
    target=os.path.realpath("/dev/dri/renderD128")
    seen=[]
    for name in os.listdir("/proc"):
        if not name.isdigit(): continue
        p=f"/proc/{name}"
        try:
            for fd in os.listdir(p+"/fd"):
                try:
                    if os.path.realpath(p+"/fd/"+fd)!=target: continue
                    cmd=Path(p+"/cmdline").read_bytes().replace(b"\0",b" ").decode(errors="replace").strip()
                    seen.append((int(name),cmd))
                    break
                except (FileNotFoundError,PermissionError,OSError):
                    pass
        except (FileNotFoundError,PermissionError,OSError):
            pass
    return seen

def wait_health(proc,timeout=180):
    end=time.monotonic()+timeout
    last=""
    while time.monotonic()<end:
        if proc.poll() is not None:
            return False,f"worker exited rc={proc.returncode}"
        try:
            with urllib.request.urlopen(f"http://{a.worker_host}:{a.worker_port}/health",timeout=1) as r:
                raw=r.read().decode("utf-8","replace")
            if '"status":"ok"' in raw.replace(" ","") or '"status": "ok"' in raw:
                return True,raw
            last=raw
        except Exception as e:
            last=repr(e)
        time.sleep(.5)
    return False,last or "health timeout"

class RouterState:
    def __init__(self):
        self.switch_lock=threading.RLock()
        self.cv=threading.Condition()
        self.worker=None
        self.worker_model=None
        self.worker_started=0.0
        self.last_used=time.monotonic()
        self.active=0
        self.gpu_fd=None
        self.embed_was_active=False
        self.speaches_was_running=False
        self.worker_log_handle=None
        self.stopping=False

    def acquire_gpu(self,timeout=120):
        if self.gpu_fd is not None: return
        fd=open(GPU_LOCK,"a+")
        end=time.monotonic()+timeout
        while True:
            try:
                fcntl.flock(fd.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic()>=end:
                    fd.close()
                    raise RuntimeError("GPU busy: timed out waiting for Cloud9 GPU lock")
                time.sleep(.25)
        was=service_active(EMBED_SERVICE)
        speaches_was=container_running(SPEACHES_CONTAINER)
        try:
            if was and embedding_busy():
                raise RuntimeError("Embedding Engine is processing a request; refusing GPU preemption")
            if was:
                run_systemctl("stop",EMBED_SERVICE,check=True,timeout=45)
                for _ in range(40):
                    if not service_active(EMBED_SERVICE): break
                    time.sleep(.25)
            if speaches_was:
                if tcp_port_busy(8005):
                    raise RuntimeError("Speaches is serving an active HTTP connection; refusing GPU preemption")
                run_docker("stop","--time","20",SPEACHES_CONTAINER,check=True,timeout=30)
                for _ in range(80):
                    if not container_running(SPEACHES_CONTAINER): break
                    time.sleep(.25)
            users=gpu_users()
            if users:
                for _ in range(80):
                    time.sleep(.25)
                    users=gpu_users()
                    if not users: break
            if users:
                raise RuntimeError("GPU render device is still in use after managed handoff: "+repr(users))
        except Exception:
            if speaches_was:
                run_docker("start",SPEACHES_CONTAINER,timeout=30)
            if was:
                run_systemctl("thaw",EMBED_SERVICE)
                run_systemctl("reset-failed",EMBED_SERVICE)
                run_systemctl("start",EMBED_SERVICE)
                run_systemctl("thaw",EMBED_SERVICE)
            fcntl.flock(fd.fileno(),fcntl.LOCK_UN)
            fd.close()
            raise
        self.embed_was_active=was
        self.speaches_was_running=speaches_was
        self.gpu_fd=fd

    def release_gpu(self):
        fd=self.gpu_fd
        was=self.embed_was_active
        speaches_was=self.speaches_was_running
        self.gpu_fd=None
        self.embed_was_active=False
        self.speaches_was_running=False
        if fd:
            try:
                fcntl.flock(fd.fileno(),fcntl.LOCK_UN)
            finally:
                fd.close()
        if was:
            run_systemctl("thaw",EMBED_SERVICE)
            run_systemctl("reset-failed",EMBED_SERVICE)
            run_systemctl("start",EMBED_SERVICE)
            run_systemctl("thaw",EMBED_SERVICE)
        if speaches_was:
            run_docker("start",SPEACHES_CONTAINER,timeout=30)

    def runtime(self,m):
        p=ENGINE/"current"/m["backend"]/"bin"/"llama-server"
        if not p.exists():
            raise RuntimeError(f"backend {m['backend']} is unavailable: {p}")
        return str(p)

    def worker_args(self,m):
        args=[
            self.runtime(m),"-m",m["model"],"-ngl","99","-c",str(m.get("context",16384)),"-np","1",
            "-b",str(m.get("batch",1024)),"-ub",str(m.get("ubatch",1024)),
            "-t","8","-tb","8","-fa",m.get("flash_attention","on"),
            "-ctk",m.get("cache_type_k","f16"),"-ctv",m.get("cache_type_v","f16"),
            "--fit","off","--jinja","--reasoning","off","--reasoning-budget","0",
            "-lm",m.get("load_mode","mmap"),"--poll","100","--poll-batch","0",
            "--host",a.worker_host,"--port",str(a.worker_port),
            "--no-warmup","--no-webui","--alias",m["id"],
        ]
        if m["backend"]!="prism":
            args += ["--lazy-mode",m.get("lazy_mode","off")]
        args += list(m.get("extra_args",[]))
        return args

    def stop_worker_locked(self):
        p=self.worker
        self.worker=None
        old=self.worker_model
        self.worker_model=None
        if p and p.poll() is None:
            p.terminate()
            try:p.wait(timeout=15)
            except subprocess.TimeoutExpired:
                p.kill()
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired: pass
        if self.worker_log_handle:
            try:self.worker_log_handle.close()
            except Exception:pass
            self.worker_log_handle=None
        self.release_gpu()
        self.last_used=time.monotonic()
        if old:
            print(f"Cloud9 router: unloaded {old}",flush=True)

    def ensure_worker_locked(self,m):
        if self.worker is not None and self.worker.poll() is None and self.worker_model==m["id"]:
            return
        model_path=Path(m["model"])
        max_bytes=int(os.environ.get("CLOUD9_ENGINE_MAX_MODEL_BYTES",catalog.get("defaults",{}).get("max_model_bytes",42949672960)))
        allow_oversize=os.environ.get("CLOUD9_ENGINE_ALLOW_OVERSIZE","0").lower() in ("1","true","yes") or bool(m.get("allow_oversize"))
        try:
            model_bytes=model_path.stat().st_size
        except FileNotFoundError:
            raise RuntimeError(f"model file is missing: {model_path}")
        if model_bytes > max_bytes and not allow_oversize:
            raise RuntimeError(
                f"refusing oversized model {m['id']}: {model_bytes} bytes > safety limit {max_bytes}; "
                "use CLOUD9_ENGINE_ALLOW_OVERSIZE=1 only for an explicit lab run"
            )
        end=time.monotonic()+600
        with self.cv:
            while self.active>0:
                left=end-time.monotonic()
                if left<=0: raise RuntimeError("timed out waiting for active requests before model switch")
                self.cv.wait(min(left,1))
        self.stop_worker_locked()
        self.acquire_gpu(timeout=int(catalog.get("defaults",{}).get("gpu_lock_timeout_seconds",120)))
        args=self.worker_args(m)
        env=os.environ.copy()
        perf=[x for x in env.get("RADV_PERFTEST","").split(",") if x]
        if "nogttspill" not in perf:perf.append("nogttspill")
        env["RADV_PERFTEST"]=",".join(perf)
        self.worker_log_handle=open(WORKER_LOG,"a",buffering=1)
        self.worker_log_handle.write(f"\n=== {time.strftime('%Y-%m-%dT%H:%M:%S%z')} {m['id']} backend={m['backend']} ===\n")
        try:
            self.worker=subprocess.Popen(args,stdout=self.worker_log_handle,stderr=subprocess.STDOUT,env=env)
            self.worker_model=m["id"]
            self.worker_started=time.monotonic()
            ok,why=wait_health(self.worker)
            if not ok:
                raise RuntimeError(f"worker failed health check: {why}")
            print(f"Cloud9 router: loaded {m['id']} via {m['backend']}",flush=True)
        except Exception:
            self.stop_worker_locked()
            raise

    def begin(self,m):
        with self.switch_lock:
            self.ensure_worker_locked(m)
            with self.cv:
                self.active+=1
                self.last_used=time.monotonic()

    def end(self):
        with self.cv:
            self.active=max(0,self.active-1)
            self.last_used=time.monotonic()
            self.cv.notify_all()

    def stop_all(self):
        with self.switch_lock:
            self.stopping=True
            with self.cv:
                end=time.monotonic()+15
                while self.active and time.monotonic()<end:
                    self.cv.wait(.5)
            self.stop_worker_locked()

state=RouterState()

def resolve_model(name):
    if not name: return None
    return model_by_id.get(name) or model_by_id.get(str(name).lower())

def json_bytes(x):
    return json.dumps(x,ensure_ascii=False,separators=(",",":")).encode()

class Handler(BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    server_version="Cloud9ModelRouter/1.0"

    def log_message(self,fmt,*args):
        sys.stderr.write("%s - %s\n"%(self.address_string(),fmt%args))

    def send_json(self,status,obj):
        data=json_bytes(obj)
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(data)))
        self.send_header("Connection","keep-alive")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","authorization,content-type")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Content-Length","0")
        self.end_headers()

    def do_GET(self):
        if self.path.rstrip("/") in ("","/health"):
            self.send_json(200,{"status":"ok","service":"cloud9-model-router","worker_model":state.worker_model})
            return
        if self.path.rstrip("/")=="/v1/models":
            data=[]
            for m in models:
                data.append({"id":m["id"],"object":"model","created":0,"owned_by":"cloud9-engine",
                             "cloud9":{"group":m.get("group"),"uncensored":m.get("uncensored"),
                                       "backend":m.get("backend"),"context":m.get("context"),
                                       "benchmark":m.get("benchmark",{})}})
            self.send_json(200,{"object":"list","data":data})
            return
        if self.path.startswith("/v1/models/"):
            mid=self.path.split("/",3)[-1]
            m=resolve_model(mid)
            if not m:self.send_json(404,{"error":{"message":"unknown model","type":"invalid_request_error"}});return
            self.send_json(200,{"id":m["id"],"object":"model","owned_by":"cloud9-engine","cloud9":m})
            return
        self.proxy_existing(None)

    def do_POST(self):
        n=int(self.headers.get("Content-Length","0") or "0")
        raw=self.rfile.read(n) if n else b""
        if self.path.rstrip("/")=="/internal/unload":
            with state.switch_lock:
                with state.cv:
                    if state.active>0:
                        self.send_json(409,{"error":{"message":"worker has active requests","type":"conflict"}})
                        return
                previous=state.worker_model
                state.stop_worker_locked()
            self.send_json(200,{"status":"ok","unloaded":previous,"worker_model":state.worker_model})
            return
        try: body=json.loads(raw or b"{}")
        except Exception:
            self.send_json(400,{"error":{"message":"invalid JSON request","type":"invalid_request_error"}});return
        m=resolve_model(body.get("model"))
        if m is None:
            self.send_json(400,{"error":{"message":"unknown or missing model; use GET /v1/models","type":"invalid_request_error"}});return
        body["model"]=m["id"]
        self.proxy_existing((m,json_bytes(body)))

    def proxy_existing(self,item):
        m=None;raw=None
        if item is not None:m,raw=item
        elif state.worker_model:
            m=resolve_model(state.worker_model)
        if m is None:
            self.send_json(503,{"error":{"message":"no worker loaded for this endpoint","type":"service_unavailable"}});return
        try:
            state.begin(m)
        except Exception as e:
            self.send_json(503,{"error":{"message":str(e),"type":"service_unavailable"}});return
        try:
            conn=http.client.HTTPConnection(a.worker_host,a.worker_port,timeout=1800)
            headers={}
            for k,v in self.headers.items():
                kl=k.lower()
                if kl not in ("host","connection","content-length","transfer-encoding"):
                    headers[k]=v
            if raw is not None:
                headers["Content-Type"]="application/json"
                headers["Content-Length"]=str(len(raw))
            conn.request(self.command,self.path,body=raw,headers=headers)
            resp=conn.getresponse()
            self.send_response(resp.status,resp.reason)
            excluded={"connection","transfer-encoding","content-length","server","date"}
            for k,v in resp.getheaders():
                if k.lower() not in excluded:self.send_header(k,v)
            length=resp.getheader("Content-Length")
            if length is not None:
                self.send_header("Content-Length",length)
                self.end_headers()
                while True:
                    chunk=resp.read(65536)
                    if not chunk:break
                    self.wfile.write(chunk)
            else:
                self.send_header("Transfer-Encoding","chunked")
                self.end_headers()
                reader=getattr(resp,"read1",resp.read)
                while True:
                    chunk=reader(65536)
                    if not chunk:break
                    self.wfile.write(("%X\r\n"%len(chunk)).encode()+chunk+b"\r\n")
                    self.wfile.flush()
                self.wfile.write(b"0\r\n\r\n");self.wfile.flush()
            conn.close()
        except (BrokenPipeError,ConnectionResetError):
            pass
        except Exception as e:
            try:self.send_json(502,{"error":{"message":repr(e),"type":"upstream_error"}})
            except Exception:pass
        finally:
            state.end()

def reaper():
    idle=a.idle_seconds or int(catalog.get("defaults",{}).get("worker_idle_seconds",30))
    while not state.stopping:
        time.sleep(2)
        if state.worker is None:continue
        with state.cv:
            due=state.active==0 and time.monotonic()-state.last_used>=idle
        if due:
            with state.switch_lock:
                with state.cv:
                    if state.active or time.monotonic()-state.last_used<idle:continue
                state.stop_worker_locked()

threading.Thread(target=reaper,name="cloud9-idle-reaper",daemon=True).start()
srv=ThreadingHTTPServer((a.host,a.port),Handler)

def shutdown(signum,frame):
    threading.Thread(target=srv.shutdown,daemon=True).start()
for sig in (signal.SIGTERM,signal.SIGINT):
    signal.signal(sig,shutdown)

print(f"Cloud9 model router listening on {a.host}:{a.port}; {len(models)} models",flush=True)
try:
    srv.serve_forever(poll_interval=.5)
finally:
    state.stop_all()
    srv.server_close()
