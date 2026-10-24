#!/usr/bin/env python3
"""Read-only native Cloud9 llama.cpp OmniRoute combo mapping audit.
No credentials or model inference; never writes the live SQLite database.
"""
import argparse
import json
import pathlib
import sqlite3
import sys
import time

def assess(db_path, catalog_path, combo_name="Cloud9-Engine"):
    db=sqlite3.connect("file:"+str(pathlib.Path(db_path).resolve())+"?mode=ro",uri=True,timeout=5)
    try:
        row=db.execute("select name,is_active,test_status,provider_specific_data from provider_connections where provider=?",("llama-cpp",)).fetchone()
        combo=db.execute("select name,data from combos where name=?",(combo_name,)).fetchone()
    finally:
        db.close()
    catalog=json.loads(pathlib.Path(catalog_path).read_text())
    active={m["id"]:m for m in catalog["models"]}
    errors=[]
    if not row:
        errors.append("OmniRoute llama-cpp provider missing")
        provider={"exists":False}
    else:
        name,enabled,status,raw=row
        raw=raw or ""
        provider={
            "exists":True,"name":name,"enabled":bool(enabled),
            "status":status,"points_to_cloud9_8090":":8090" in raw,
        }
        if not enabled or ":8090" not in raw:
            errors.append("Native Cloud9 provider is inactive or has wrong endpoint")
    if not combo:
        errors.append("Native Cloud9 combo missing")
        combo_info={"exists":False,"name":combo_name,"models":[]}
    else:
        name,blob=combo
        config=json.loads(blob)
        raw_models=config.get("models",[])
        members=[]
        for m in raw_models:
            identifier=m.get("model","") if isinstance(m,dict) else ""
            if not identifier.startswith("llama-cpp/Cloud9-"):
                errors.append("Unsupported or nonlocal model reference in Cloud9 combo")
                continue
            model=identifier.removeprefix("llama-cpp/")
            members.append({"id":model,"exists_in_router_catalog":model in active,
                "group":active.get(model,{}).get("group"),
                "uncensored":active.get(model,{}).get("uncensored")})
            if model not in active:
                errors.append("Combo model not in native catalog: "+model)
        combo_info={"exists":True,"name":name,"strategy":config.get("strategy"),
            "model_count":len(members),"models":members}
    chosen=["Cloud9-MiniCPM5-2B-DSpark","Cloud9-Qwen3.8-4B-Heretic",
            "Cloud9-Pym-35B-A3B-MTP","Cloud9-Qwen3.6-35B-A3B-Heretic"]
    included={m["id"] for m in combo_info.get("models",[])}
    roles={model:{"catalog_available":model in active,"in_native_cloud9_combo":model in included} for model in chosen}
    # Access via native provider is independent of inclusion in a named combo.
    return {"checked_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
       "mode":"read-only","native_provider":provider,"combo":combo_info,
       "selected_roles":roles,"errors":errors,
       "static_native_connection_valid":not bool(errors),
       "model_inference_certified":False,
       "all_agents_integrated":False,
       "single_generation_worker_caveat":True}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--omniroute-db",required=True)
    a.add_argument("--catalog",required=True)
    a.add_argument("--output")
    opt=a.parse_args()
    result=assess(opt.omniroute_db,opt.catalog)
    s=json.dumps(result,indent=2,ensure_ascii=False)
    if opt.output:pathlib.Path(opt.output).write_text(s+"\n")
    print(s)
    sys.exit(2 if result["errors"] else 0)

if __name__=="__main__":main()
