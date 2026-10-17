#!/usr/bin/env python3
"""Same-GGUF Vulkan engine comparison. Requires host CT410 arbiter/guard lock."""
import argparse, hashlib, json, os, re, signal, subprocess, time, urllib.request
from pathlib import Path
ROOT=Path(os.environ.get("CLOUD9_MOTEURS_ROOT",str(Path.home()/"Projets/HomeLab/Moteurs IA")))
BASE=ROOT/"Sources/Builds"
STORE=Path(os.environ.get("CLOUD9_GGUF_ROOT","/srv/storage/nvme/ai-models/llm/gguf"))
OUT=Path(os.environ.get("CLOUD9_BENCH_OUT",str(ROOT/"Sources/Benchmarks/Engine-Tournament/2026-10-18")))
ENGINES={
 "atomic-2.0":BASE/"atomic-turboquant-2.0.0-20261016/build-cloud9/bin/llama-server",
 "atomic-dev":BASE/"atomic-dev-20261017-3cde9e4/bin/llama-server",
 "llama-v070":BASE/"llama-v070-20261015/build-cloud9/bin/llama-server",
 "llama-oct17":BASE/"llama-upstream-20261017-9d1878a/bin/llama-server",
 "llama-s1":BASE/"llama-s1-v61-20261018/bin/llama-server",
}
PORT=18220
TOOL={"type":"function","function":{"name":"calendar_lookup","description":"Read-only calendar lookup by ISO date.","parameters":{"type":"object","properties":{"date":{"type":"string"}},"required":["date"]}}}
def api(url,data=None,timeout=150):
    payload=json.dumps(data,ensure_ascii=False).encode() if data is not None else None
    req=urllib.request.Request(f"http://127.0.0.1:{PORT}{url}",data=payload,headers={"Content-Type":"application/json"} if payload else {})
    with urllib.request.urlopen(req,timeout=timeout) as resp:return json.load(resp)
def cases():
    return {
     "json":{"messages":[{"role":"user","content":"Réponds uniquement en JSON valide, sans markdown. 13 + 18 pommes. Trois champs exactement : total (nombre), ville (Toulouse), date (2026-10-19)."}],"max_tokens":100},
     "tool":{"messages":[{"role":"user","content":"Consulte mon calendrier du 19 octobre 2026. Tu dois appeler l'outil calendar_lookup en lecture seule, avec une date ISO YYYY-MM-DD, sans autre texte."}],"tools":[TOOL],"tool_choice":"auto","max_tokens":100},
     "code":{"messages":[{"role":"user","content":"Répare le bug : def add(a,b): return a-b. Réponds uniquement en JSON strict avec une seule clé corrected_line et comme valeur le texte exact de la ligne corrigée, précédée de quatre espaces."}],"max_tokens":100},
     "creative":{"messages":[{"role":"user","content":"Rédige un mini-monologue comique français à la première personne de 35 à 80 mots. Trois mots obligatoires : dinosaures, batterie, dentiste. Pas de titre ni de liste."}],"max_tokens":140},
     "prefill":{"messages":[{"role":"user","content":"Réponds seulement en JSON {\"marqueur\":\"LYRA-738\"} si ce marqueur est dans ce dossier. MARQUEUR=LYRA-738\n"+("Compte rendu fictif Toulouse 2026, aucun renseignement personnel, distraction alpha beta gamma.\n"*95)+"FIN."}],"max_tokens":70}
    }
def correct(kind,msg):
    s=(msg.get("content") or "").strip()
    # Literal JSON is required. Markdown fencing is NOT valid protocol output.
    if kind=="tool":
        if s or len(msg.get("tool_calls") or [])!=1:return False
        for call in msg.get("tool_calls") or []:
            f=call.get("function") or {}
            try:
                if f.get("name")=="calendar_lookup" and json.loads(f.get("arguments") or "{}")=={"date":"2026-10-19"}:return True
            except (ValueError,TypeError):pass
        return False
    if kind in ("json","code","prefill"):
        try:obj=json.loads(s)
        except (ValueError,TypeError):return False
        return obj==({"json":{"total":31,"ville":"Toulouse","date":"2026-10-19"},"code":{"corrected_line":"    return a + b"},"prefill":{"marqueur":"LYRA-738"}}[kind])
    words=re.findall(r"\b[\wÀ-ÿ-]+\b",s.lower())
    return 35<=len(words)<=80 and all(x in words for x in ("dinosaures","batterie","dentiste")) and bool(re.search(r"\b(je|j'|mon|moi)\b",s.lower()))
def semantic_code_correct(msg):
    txt=msg.get("content") or ""
    return bool(re.search(r"\breturn\s+a\s*\+\s*b\b",txt))
def tctl():
    for p in Path("/sys/class/hwmon").glob("hwmon*/name"):
        try:
            if p.read_text().strip()=="k10temp":return int((p.parent/"temp1_input").read_text())/1000
        except (OSError,ValueError):pass
    raise RuntimeError("Tctl not readable; no GPU bench")
def cool_to(target=74.0,max_seconds=75):
    began=time.monotonic()
    while tctl()>target:
        if time.monotonic()-began>max_seconds:raise RuntimeError(f"Tctl cooling failure: {tctl()}C")
        time.sleep(4)
    return round(time.monotonic()-began,2)
def terminate(p):
    if p and p.poll() is None:
        os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=15)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=8)
def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--engine",required=True,choices=list(ENGINES))
    arg.add_argument("--filename",required=True)
    arg.add_argument("--repeats",type=int,default=3)
    arg.add_argument("--case",choices=["all","agentic",*cases()],default="agentic")
    a=arg.parse_args()
    assert os.getenv("CLOUD9_GPU_COEXIST_ADMITTED")=="1"
    assert a.repeats>=3 and "/" not in a.filename and a.filename.endswith(".gguf")
    eng=ENGINES[a.engine];model=STORE/a.filename
    assert eng.is_file() and model.is_file() and model.stat().st_size<14_000_000_000
    OUT.mkdir(parents=True,exist_ok=True)
    tag=f"{a.engine}-{model.stem[:24]}-{a.case}-protocol-strict-v2"
    out=OUT/f"{tag}.json"; log=OUT/f"{tag}.log"
    assert not out.exists() and not log.exists(),"refusing overwrite existing evidence"
    suite=cases() if a.case=="all" else ({k:cases()[k] for k in ("json","tool","code")} if a.case=="agentic" else {a.case:cases()[a.case]})
    result={"date":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"engine":a.engine,"engine_sha256":hashlib.sha256(eng.read_bytes()).hexdigest(),"gguf":model.name,
            "gguf_path":str(model),"backend":"Vulkan RADV PHOENIX gfx1103","ctx_size":8192,"kv_cache":"F16/F16","speculative":False,
            "gpu_layers":99,"flash_attention":"on","temperature":0,"seed":42,"repeats":a.repeats,"rows":[],"status":"started","production_eligible":False}
    p=None
    try:
        with log.open("w") as f:
            args=[str(eng),"-m",str(model),"--host","127.0.0.1","--port",str(PORT),"-c","8192","-ngl","99","-np","1",
                  "-b","512","-ub","512","--flash-attn","on","--fit","off","--no-warmup","--no-webui","--no-context-shift",
                  "--jinja","--reasoning","off","--reasoning-budget","0","-ctk","f16","-ctv","f16"]
            p=subprocess.Popen(args,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,
                  env={**os.environ,"LD_LIBRARY_PATH":str(eng.parent)+":"+os.getenv("LD_LIBRARY_PATH","")})
            start=time.monotonic()
            for n in range(120):
                if p.poll() is not None:raise RuntimeError("worker exited rc="+str(p.returncode))
                try:
                    if api("/health",timeout=2).get("status")=="ok":break
                except Exception:pass
                time.sleep(.3)
            else:raise RuntimeError("loading timeout")
            result["load_s"]=round(time.monotonic()-start,3)
            print("A_B_LOADED",a.engine,model.name,result["load_s"],flush=True)
            for rep in range(a.repeats):
                for key,opts in suite.items():
                    req={"model":str(model),"seed":42,"temperature":0,"stream":False,
                         "enable_thinking":False,"cache_prompt":False,**opts}
                    wait=cool_to()
                    temp_before=tctl()
                    st=time.monotonic()
                    data=api("/v1/chat/completions",req)
                    msg=data["choices"][0]["message"]
                    timing=data.get("timings") or {};used=data.get("usage") or {}
                    temp_after=tctl()
                    row={"case":key,"rep":rep+1,"correct":correct(key,msg),"wall_s":round(time.monotonic()-st,3),
                         "cooling_s":wait,"tctl_before":temp_before,"tctl_after":temp_after,
                         "prefill_tps":timing.get("prompt_per_second"),"decode_tps":timing.get("predicted_per_second"),
                         "semantic_code_correct":semantic_code_correct(msg) if key=="code" else None,
                         "prompt_tokens":used.get("prompt_tokens"),"completion_tokens":used.get("completion_tokens"),"message":msg}
                    result["rows"].append(row)
                    if temp_after>=79.0:
                        raise RuntimeError(f"Thermal ceiling near 80C: {temp_after}")
                    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
                    print("A_B_CASE",a.engine,key,rep+1,"OK",row["correct"],"WALL",row["wall_s"],"DECODE",row["decode_tps"],flush=True)
            result["status"]="complete"
    except Exception as e:
        result["status"]="error";result["error"]=repr(e)
        print("A_B_ERROR",a.engine,repr(e),flush=True)
    finally:
        terminate(p)
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        print("A_B_ENDED",a.engine,result["status"],out,flush=True)
    if result["status"]!="complete":raise SystemExit(4)
if __name__=="__main__":main()
