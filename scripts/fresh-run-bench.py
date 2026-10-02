#!/usr/bin/env python3
import argparse,json,os,statistics,subprocess,time,urllib.request
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--runtime",required=True)
ap.add_argument("--model",required=True)
ap.add_argument("--runs",type=int,default=5)
ap.add_argument("--port",type=int,default=19892)
ap.add_argument("--tokens",type=int,default=256)
ap.add_argument("--spec",choices=["none","mtp"],default="none")
ap.add_argument("--output",required=True)
a=ap.parse_args()
prompt=(Path(__file__).resolve().parents[1]/"bench/prompt.txt").read_text()
def req(url,body=None,timeout=600):
    data=None if body is None else json.dumps(body).encode()
    r=urllib.request.Request(url,data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=timeout) as x:return json.load(x)
def wait(port,p,limit=180):
    for _ in range(limit):
        if p.poll() is not None:return False
        try:
            if req(f"http://127.0.0.1:{port}/health",timeout=2).get("status")=="ok":return True
        except:pass
        time.sleep(1)
    return False
try:
    runtime_help=subprocess.check_output([a.runtime,"--help"],text=True,stderr=subprocess.STDOUT,timeout=15)
except Exception:
    runtime_help=""
rows=[]
for n in range(a.runs):
    log=Path(a.output).with_suffix(f".run{n+1}.log").open("w")
    args=[a.runtime,"-m",a.model,"-ngl","99","-c","8192","-np","1",
          "-b","1024","-ub","1024","-t","8","-tb","8","-fa","on","--fit","off",
          "--jinja","-lm","mmap","--poll","100","--poll-batch","0",
          "--host","127.0.0.1","--port",str(a.port),"--no-warmup","--alias","fresh-bench"]
    if "--lazy-mode" in runtime_help:
        args += ["--lazy-mode","off"]
    if a.spec=="mtp":
        args += ["--spec-type","draft-mtp","--spec-draft-n-max","2","--spec-draft-p-min","0",
                 "--no-spec-draft-backend-sampling"]
    env=os.environ.copy()
    env["RADV_PERFTEST"]=",".join(x for x in [env.get("RADV_PERFTEST",""),"nogttspill"] if x).strip(",")
    t0=time.monotonic()
    p=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT,env=env)
    try:
        if not wait(a.port,p):
            rows.append({"run":n+1,"status":"load-failed","load_s":time.monotonic()-t0})
            continue
        load=time.monotonic()-t0
        body={"model":"fresh-bench","messages":[{"role":"user","content":prompt}],
              "temperature":0.0,"seed":42,"max_tokens":a.tokens,"cache_prompt":False,
              "chat_template_kwargs":{"enable_thinking":False}}
        t=time.monotonic(); j=req(f"http://127.0.0.1:{a.port}/v1/chat/completions",body); wall=time.monotonic()-t
        tm=j.get("timings",{})
        rows.append({"run":n+1,"status":"ok","load_s":load,"wall_s":wall,
                     "prefill_tps":tm.get("prompt_per_second",0.0),
                     "decode_tps":tm.get("predicted_per_second",0.0),
                     "draft_n":tm.get("draft_n"),"draft_accepted":tm.get("draft_n_accepted")})
    except Exception as e:
        rows.append({"run":n+1,"status":"error","error":repr(e)})
    finally:
        if p.poll() is None:
            p.terminate()
            try:p.wait(timeout=12)
            except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
        log.close()
        time.sleep(2)
ok=[x for x in rows if x.get("status")=="ok"]
res={"runtime":a.runtime,"model":a.model,"spec":a.spec,"runs":rows}
if ok:
    res["median_decode_tps"]=statistics.median(x["decode_tps"] for x in ok)
    res["median_prefill_tps"]=statistics.median(x["prefill_tps"] for x in ok)
    res["median_load_s"]=statistics.median(x["load_s"] for x in ok)
Path(a.output).write_text(json.dumps(res,indent=2)+"\n")
print(json.dumps(res,indent=2))
