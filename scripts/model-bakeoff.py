#!/usr/bin/env python3
import argparse,json,os,re,statistics,subprocess,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser()
ap.add_argument("--manifest",default=str(ROOT/"bench/model-bakeoff-20260928.json"))
ap.add_argument("--fixture",default=str(ROOT/"bench/fixtures/dpafm48.json"))
ap.add_argument("--only",default="")
ap.add_argument("--port",type=int,default=19890)
ap.add_argument("--runs",type=int,default=3)
ap.add_argument("--context",type=int,default=16384)
ap.add_argument("--speed-only",action="store_true")
ap.add_argument("--speed-tokens",type=int,default=256)
a=ap.parse_args()
manifest=json.load(open(a.manifest))
fixture=json.load(open(a.fixture))
run_date=datetime.now().astimezone().date().isoformat()
outdir=ROOT/"bench/results"/run_date
outdir.mkdir(parents=True,exist_ok=True)
slot_dir=outdir/"slot-cache"
slot_dir.mkdir(parents=True,exist_ok=True)
selected=set(x for x in a.only.split(",") if x)
def http_json(url,body=None,timeout=900):
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(url,data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r: return json.load(r)
def health(port,pid,limit=180):
    for _ in range(limit):
        if pid.poll() is not None: return False
        try:
            if http_json(f"http://127.0.0.1:{port}/health",timeout=2).get("status")=="ok": return True
        except Exception: pass
        time.sleep(1)
    return False
def stop_server(p):
    if p.poll() is not None: return
    p.terminate()
    try: p.wait(timeout=8)
    except subprocess.TimeoutExpired:
        p.kill(); p.wait(timeout=5)
def erase_slot(port):
    try:
        http_json(f"http://127.0.0.1:{port}/slots/0?action=erase",{},timeout=10)
    except Exception:
        # Some fork builds may not expose slot erase; request-level cache_prompt=false still applies.
        pass
def timed_chat(port,messages,max_tokens=256,temp=0.0,response_format=None):
    erase_slot(port)
    body={"model":"bakeoff","messages":messages,"temperature":temp,"seed":42,
          "max_tokens":max_tokens,"cache_prompt":False,
          "chat_template_kwargs":{"enable_thinking":False}}
    if response_format is not None:
        body["response_format"]=response_format
    t=time.monotonic()
    j=http_json(f"http://127.0.0.1:{port}/v1/chat/completions",body)
    wall=time.monotonic()-t
    tm=j.get("timings",{})
    usage=j.get("usage",{})
    completion_tokens=usage.get("completion_tokens") or tm.get("predicted_n") or 0
    effective_output_tps=(completion_tokens/wall) if wall > 0 and completion_tokens else 0.0
    return {"wall_s":wall,"prefill_tps":tm.get("prompt_per_second",0.0),
            "decode_tps":tm.get("predicted_per_second",0.0),
            "effective_output_tps":effective_output_tps,
            "completion_tokens":completion_tokens,
            "draft_n":tm.get("draft_n"),"draft_accepted":tm.get("draft_n_accepted"),
            "content":(j["choices"][0]["message"].get("content") or
                       j["choices"][0]["message"].get("reasoning_content") or "")}
def quality_prompt(f):
    return f"""Tu es la première partie éditoriale d'AutoPublisher V21.
À partir UNIQUEMENT du transcript ci-dessous, retourne UN objet JSON sans markdown avec exactement:
episode_topic, premise, chapters, title, caption, youtube_title, short_caption.
chapters = EXACTEMENT 6 objets {{time,title}}; premier chapitre exactement 00:00; chaque time doit provenir d'un timecode réellement présent; ordre chronologique.
title = "Dernier Podcast Avant la Fin du Monde - 48 - <sujet>".
caption = français, 80 à 240 caractères, concrète, sarcastique/sec si pertinent, ne spoile pas tout; pas de marketing générique; aucune répétition de mot ou d’idée.
youtube_title = précis et accrocheur sans clickbait mensonger.
short_caption = une seule phrase courte.
Invités connus: Kenny Vago, Emma de Foucaud. N'invente ni invité, ni citation, ni URL, ni fait absent.
TRANSCRIPT:
{f['transcript_pack']}"""
def parse_json_text(s):
    s=s.strip(); fence=chr(96)*3
    if s.startswith(fence): s=re.sub(r"^.{3}(?:json)?\s*|\s*.{3}$","",s,flags=re.S)
    try: return json.loads(s)
    except Exception:
        i=s.find("{"); j=s.rfind("}")
        if i>=0 and j>i:
            try: return json.loads(s[i:j+1])
            except Exception: return None
    return None
def tc_seconds(s):
    try:
        p=[int(x) for x in str(s).split(":")]
        return p[-1]+60*p[-2]+(3600*p[-3] if len(p)>2 else 0)
    except Exception: return -1
def score_quality(content,f):
    obj=parse_json_text(content); detail={}
    if not isinstance(obj,dict): return 0,{"json_valid":False},None
    score=20; detail["json_valid"]=True
    req=["episode_topic","premise","chapters","title","caption","youtube_title","short_caption"]
    present=sum(k in obj and obj[k] not in (None,"",[]) for k in req)
    score+=20*present/len(req); detail["required"]=present
    ch=obj.get("chapters",[]); good_n=isinstance(ch,list) and len(ch)==6
    if good_n: score+=10
    detail["chapters_count"]=len(ch) if isinstance(ch,list) else -1
    times=[str(x.get("time","")) for x in ch if isinstance(x,dict)] if isinstance(ch,list) else []
    if times and times[0]=="00:00": score+=5
    allowed=set(f["allowed_timecodes"])|{"00:00"}
    grounded=bool(times) and all(t in allowed for t in times)
    if grounded: score+=15
    detail["timecodes_grounded"]=grounded
    sec=[tc_seconds(t) for t in times]
    monotonic=bool(sec) and all(x>=0 for x in sec) and sec==sorted(sec)
    if monotonic: score+=5
    detail["timecodes_monotonic"]=monotonic
    title=str(obj.get("title",""))
    if title.startswith("Dernier Podcast Avant la Fin du Monde - 48 - "): score+=5
    caption=str(obj.get("caption",""))
    generic=bool(re.search(r"ne manquez pas|plongez|découvrez cet épisode|épisode incontournable|rejoignez-nous",caption,re.I))
    if not generic: score+=5
    if 80<=len(caption)<=240: score+=5
    names=(title+" "+caption+" "+str(obj.get("premise",""))).lower()
    if "kenny" in names and "emma" in names: score+=5
    detail.update({"generic_marketing":generic,"caption_chars":len(caption),"score":round(score,2)})
    return round(score,2),detail,obj

def agentic_probe(port):
    tools=[
      {"type":"function","function":{"name":"search_transcript","description":"Retrouve un transcript de podcast par identifiant.",
        "parameters":{"type":"object","properties":{"episode_id":{"type":"string"}},"required":["episode_id"]}}},
      {"type":"function","function":{"name":"create_social_draft","description":"Crée le brouillon social structuré pour une plateforme.",
        "parameters":{"type":"object","properties":{"episode_id":{"type":"string"},"platform":{"type":"string"},"tone":{"type":"string"}},
                      "required":["episode_id","platform"]}}}
    ]
    def call(messages):
        erase_slot(port)
        body={"model":"bakeoff","messages":messages,"tools":tools,"tool_choice":"auto",
              "temperature":0.0,"seed":42,"max_tokens":384,"cache_prompt":False,
              "chat_template_kwargs":{"enable_thinking":False}}
        t=time.monotonic()
        j=http_json(f"http://127.0.0.1:{port}/v1/chat/completions",body)
        return j,time.monotonic()-t
    score=0; detail={}
    m1=[{"role":"system","content":"Tu es un agent. Utilise les outils quand ils sont nécessaires; n'invente jamais leur résultat."},
        {"role":"user","content":"Prépare Instagram pour l'épisode DPAFM48. Tu dois d'abord retrouver son transcript avec l'outil prévu."}]
    j1,w1=call(m1)
    msg1=j1["choices"][0]["message"]
    calls1=msg1.get("tool_calls") or []
    ok1=False; args1={}
    if calls1:
        fn=calls1[0].get("function",{})
        try: args1=json.loads(fn.get("arguments","{}"))
        except Exception: args1={}
        ok1=fn.get("name")=="search_transcript" and args1.get("episode_id")=="DPAFM48"
    if ok1: score+=50
    detail["step1_search_transcript"]=ok1
    detail["step1_tool_calls"]=calls1
    ok2=False; calls2=[]; w2=0.0
    if calls1:
        assistant={"role":"assistant","content":msg1.get("content") or "","tool_calls":calls1}
        tool_msg={"role":"tool","tool_call_id":calls1[0].get("id","call_1"),
                  "content":json.dumps({"episode_id":"DPAFM48","topic":"Le stand-up","guests":["Kenny Vago","Emma de Foucaud"]},ensure_ascii=False)}
        j2,w2=call(m1+[assistant,tool_msg,
            {"role":"user","content":"Le transcript est retrouvé. Crée maintenant le brouillon Instagram via l'outil, ton sarcastique et court."}])
        msg2=j2["choices"][0]["message"]; calls2=msg2.get("tool_calls") or []
        if calls2:
            fn=calls2[0].get("function",{})
            try: args2=json.loads(fn.get("arguments","{}"))
            except Exception: args2={}
            ok2=(fn.get("name")=="create_social_draft" and args2.get("episode_id")=="DPAFM48"
                 and str(args2.get("platform","")).lower()=="instagram")
    if ok2: score+=50
    detail["step2_create_social_draft"]=ok2
    detail["step2_tool_calls"]=calls2
    return {"score":score,"checks":detail,"wall_s":w1+w2}

_help_cache={}
def runtime_supports(runtime, flag):
    if runtime not in _help_cache:
        try:
            _help_cache[runtime]=subprocess.check_output([runtime,"--help"],text=True,stderr=subprocess.STDOUT,timeout=15)
        except Exception:
            _help_cache[runtime]=""
    return flag in _help_cache[runtime]
def server_args(m,port):
    x=[m["runtime"],"-m",m["model"],"-ngl","99","-c",str(a.context),"-np","1",
       "-b","1024","-ub","1024","-t","8","-tb","8","-fa","on","--fit","off",
       "--jinja","-lm","mmap","--poll","100","--poll-batch","0",
       "--slot-save-path",str(slot_dir),
       "--host","127.0.0.1","--port",str(port),"--no-warmup","--alias","bakeoff"]
    if runtime_supports(m["runtime"],"--lazy-mode"):
        x += ["--lazy-mode","off"]
    if runtime_supports(m["runtime"],"--no-cache-prompt"):
        x += ["--no-cache-prompt"]
    if runtime_supports(m["runtime"],"--reasoning"):
        x += ["--reasoning","off"]
    if runtime_supports(m["runtime"],"--reasoning-budget"):
        x += ["--reasoning-budget","0"]
    if runtime_supports(m["runtime"],"-ctk") or runtime_supports(m["runtime"],"--cache-type-k"):
        x += ["-ctk","f16"]
    if runtime_supports(m["runtime"],"-ctv") or runtime_supports(m["runtime"],"--cache-type-v"):
        x += ["-ctv","f16"]
    if m.get("spec")=="inline":
        x += ["--spec-type","draft-mtp","--spec-draft-n-max","2","--spec-draft-p-min","0",
              "--no-spec-draft-backend-sampling"]
    elif m.get("spec")=="draft":
        x += ["--model-draft",m["draft"],"--spec-type","draft-mtp","--spec-draft-n-max","2",
              "--spec-draft-p-min","0","--no-spec-draft-backend-sampling"]
    elif m.get("spec")=="dspark":
        x += ["--model-draft",m["draft"],"--spec-type","draft-dspark","--spec-draft-n-max","7",
              "--spec-draft-p-min","0.6","--spec-draft-ngl","99"]
    x += list(m.get("extra_args",[]))
    return x
rows=[]
speed_prompt=(ROOT/"bench/prompt.txt").read_text()
for m in manifest["models"]:
    mid=m["id"]
    if selected and mid not in selected: continue
    result={"id":mid,"group":m.get("group"),"uncensored":m.get("uncensored"),
            "spec":m.get("spec"),"source":m.get("source"),"model":m.get("model"),
            "runtime":m.get("runtime"),"started_at":datetime.now(timezone.utc).isoformat()}
    if m.get("status")=="blocked-memory":
        result.update({"status":"skipped","reason":m["reason"]}); rows.append(result)
        (outdir/f"{mid}.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)); continue
    missing=[p for p in [m.get("runtime"),m.get("model"),m.get("draft")] if p and not Path(p).exists()]
    if missing:
        result.update({"status":"missing","missing":missing}); rows.append(result)
        (outdir/f"{mid}.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)); continue
    result["model_bytes"]=Path(m["model"]).stat().st_size
    try:
        result["runtime_version"]=subprocess.check_output([m["runtime"],"--version"],text=True,
                                                          stderr=subprocess.STDOUT,timeout=10).splitlines()[:3]
    except Exception as e: result["runtime_version_error"]=repr(e)
    log=open(outdir/f"{mid}.server.log","w")
    env=os.environ.copy()
    env["RADV_PERFTEST"]=",".join(x for x in [env.get("RADV_PERFTEST",""),"nogttspill"] if x).strip(",")
    args=server_args(m,a.port); result["server_args"]=args[1:]
    t0=time.monotonic(); p=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT,env=env)
    try:
        if not health(a.port,p):
            result.update({"status":"load-failed","load_s":time.monotonic()-t0})
        else:
            result["load_s"]=time.monotonic()-t0
            perf=[]
            for _ in range(a.runs):
                x=timed_chat(a.port,[{"role":"user","content":speed_prompt}],a.speed_tokens,0.0)
                x.pop("content",None); perf.append(x)
                time.sleep(1)
            result["performance"]={"runs":perf,
              "median_decode_tps":statistics.median(x["decode_tps"] for x in perf),
              "median_effective_output_tps":statistics.median(x["effective_output_tps"] for x in perf),
              "median_prefill_tps":statistics.median(x["prefill_tps"] for x in perf),
              "median_wall_s":statistics.median(x["wall_s"] for x in perf)}
            if a.speed_only:
                result["status"]="ok"
                rows.append(result)
                (outdir/f"{mid}.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
                continue
            quality_schema={
              "type":"object",
              "properties":{
                "episode_topic":{"type":"string","minLength":5,"maxLength":180},
                "premise":{"type":"string","minLength":20,"maxLength":240},
                "chapters":{"type":"array","minItems":6,"maxItems":6,
                            "items":{"type":"object","properties":{
                                      "time":{"type":"string","minLength":4,"maxLength":8},
                                      "title":{"type":"string","minLength":2,"maxLength":120}},
                                     "required":["time","title"],"additionalProperties":False}},
                "title":{"type":"string","minLength":10,"maxLength":180},
                "caption":{"type":"string","minLength":40,"maxLength":240},
                "youtube_title":{"type":"string","minLength":10,"maxLength":180},
                "short_caption":{"type":"string","minLength":10,"maxLength":120}
              },
              "required":["episode_topic","premise","chapters","title","caption","youtube_title","short_caption"],
              "additionalProperties":False
            }
            q=timed_chat(a.port,[{"role":"system","content":"Tu es un éditeur de podcast français rigoureux."},
                                 {"role":"user","content":quality_prompt(fixture)}],700,0.2,
                         {"type":"json_schema","json_schema":{"name":"autopublisher_editorial","strict":True,"schema":quality_schema}})
            score,detail,obj=score_quality(q["content"],fixture)
            result["quality"]={"score":score,"checks":detail,"wall_s":q["wall_s"],
                               "prefill_tps":q["prefill_tps"],"decode_tps":q["decode_tps"],
                               "draft_n":q["draft_n"],"draft_accepted":q["draft_accepted"],
                               "parsed":obj,"raw":q["content"]}
            try:
                result["agentic"]=agentic_probe(a.port)
            except Exception as e:
                result["agentic"]={"score":0,"error":repr(e)}
            result["status"]="ok"
    except Exception as e:
        result.update({"status":"error","error":repr(e)})
    finally:
        stop_server(p); log.close()
    rows.append(result)
    (outdir/f"{mid}.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
# Rebuild the index from every persisted per-model JSON so batched --only runs accumulate.
indexed=[]
for rp in sorted(outdir.glob("*.json")):
    if rp.name=="summary.json": continue
    try:
        r=json.loads(rp.read_text())
        if isinstance(r,dict) and r.get("id"): indexed.append(r)
    except Exception: pass
indexed.sort(key=lambda r:(0 if r.get("group")=="small" else 1,r.get("id","")))
summary={"date":run_date,"fixture":fixture["id"],"results":indexed}
(outdir/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False))
lines=[f"# Cloud9 model bake-off — {run_date}","",
       "| Model | Groupe | Uncens. | Spec | État | GiB | Decode t/s | Prefill t/s | AutoPublisher /100 | Agentique /100 | Load s |",
       "|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|"]
for r in indexed:
    p=r.get("performance",{}); q=r.get("quality",{}); ag=r.get("agentic",{})
    load=round(r.get("load_s",0),2) if "load_s" in r else ""
    gib=round(r.get("model_bytes",0)/(1024**3),2) if r.get("model_bytes") else ""
    lines.append(f"| {r['id']} | {r.get('group','')} | {r.get('uncensored','')} | {r.get('spec','')} | {r.get('status','')} | {gib} | {p.get('median_decode_tps','')} | {p.get('median_prefill_tps','')} | {q.get('score','')} | {ag.get('score','')} | {load} |")
(outdir/"summary.md").write_text("\n".join(lines)+"\n")
print(json.dumps({"output":str(outdir),"this_run":len(rows),"indexed":len(indexed)},indent=2))
