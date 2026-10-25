#!/usr/bin/env python3
"""Fail-closed on-host engine comparison; source-backed, no service mutations."""
from __future__ import annotations
import json,statistics
from pathlib import Path

ROOT=Path("/srv/storage/nvme/DEV/Projets/HomeLab/Moteurs IA")
ATOMIC16=ROOT/"Sources/Benchmarks/Engine-Tournament/2026-10-22/atomic-turboquant2-qwen4b-mtp2-q8turbo3-needle5-16384-reps3.json"
ATOMIC36=ROOT/"Sources/Benchmarks/Engine-Tournament/2026-10-22/atomic4b-quality12x3-mtp2-20261022.json"
CHIMERA36=ROOT/"Sources/Worklogs/2026-10-25_CHIMERA_C09_CHECKPOINT_36OF36_VERIFIED.json"
CHIMERA8=ROOT/"Sources/Worklogs/2026-10-25_CHIMERA_C08_8K_SEED3_SUCCESS_ZRAM2.json"
CHIMERA16FAIL=ROOT/"Sources/Worklogs/2026-10-25_C08_NATIVE_16K_WATCHDOG_FAIL_NO_SCORE.json"
ATOMIC_LIVE=Path("/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/atomic2-vulkan-lab-20261025/atomic2-c09-qwen4b-native-20261026.json")
STAGE=ROOT/"Sources/Worklogs/2026-10-26_ATOMIC2_EXACT_ENGINE_STAGED_LAB.json"

def load(p):return json.loads(Path(p).read_text())

def decision():
    long16=load(ATOMIC16)
    qa36=load(ATOMIC36)
    c09=load(CHIMERA36)
    c8=load(CHIMERA8)
    c16=load(CHIMERA16FAIL)
    stage=load(STAGE)
    assert long16["status"]=="retrieval_pass"
    assert long16["long_context_pass"] is True and len(long16["rows"])==3
    assert all(x["correct_all_five"] and x["correct_markers"]==5 and x["prompt_tokens_observed"]>=16000 for x in long16["rows"])
    assert long16["model"]==qa36["model"]=="Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf"
    assert qa36["model_bytes"]==long16.get("gguf_bytes",qa36["model_bytes"])==2790000800
    assert qa36["engine_sha256"]=="8ddf5bf86d78797e72a1d82ccc23a48875887427eefde8464bd72f6bb1705e85"
    assert stage["original_launcher_sha256"]==qa36["engine_sha256"]
    assert not stage["production_promoted"]
    assert c09["status"]=="complete" and len(c09["results"])==36
    assert all(x["passed"] and x["strict_json"] and not x["unsafe"] for x in c09["results"])
    assert c8["rows"][0]["five_correct"] and c8["rows"][0]["full_prompt_ingested"]
    assert c16["status"]=="inference_failed_or_watchdog" and len(c16.get("rows",[]))==0
    # The historical 36-case QA is a different rubric from C09, never
    # compare their raw percentages as matched A/B performance.
    q=qa36["quality"]
    assert len(qa36["rows"])==36 and all(q[k]["n"]==9 for k in ("json","tools","code","fr"))
    quality_categories={
       "json_strict":f'{q["json"]["correct"]}/9',
       "tool":f'{q["tools"]["correct"]}/9',
       "code":f'{q["code"]["correct"]}/9',
       "french":f'{q["fr"]["correct"]}/9',
    }
    atomic_live=None
    if ATOMIC_LIVE.exists():
        data=load(ATOMIC_LIVE)
        rows=data.get("results",[])
        atomic_live={"status":data.get("status"),"scored_cases":len(rows),
                     "safe_correct_cases":sum(x.get("passed") is True and not x.get("unsafe",False) for x in rows),
                     "unsafe_cases":sum(bool(x.get("unsafe")) for x in rows),
                     "same_fixtures_as_chimera_c09":data.get("fixture_sha256")==c09.get("fixture_sha256"),
                     "production_pass":data.get("status")=="complete" and len(rows)==36 and
                         all(x.get("passed") and not x.get("unsafe") for x in rows)}
    return {
      "hardware":"Cloud9 Ryzen7 8845HS / 96 GiB / Radeon 780M gfx1103 12 CUs, Proxmox Linux",
      "source_lineage":"Actual local GPU validations only; benchmarks across different protocols are NOT directly comparable",
      "winner_speed_and_verified_16K_recall":"Atomic TurboQuant 2.0.0 Vulkan, Qwen3.5 4B MTP Q4_K_M",
      "atomic2":{"historical_16K_exact_retrieval":"3/3 five markers, 16330 actual input tokens",
         "historical_16K_median_decode_tps":round(statistics.median(row["decode_tps"] for row in long16["rows"]),4),
         "historical_16K_median_prefill_tps":round(statistics.median(row["prefill_tps"] for row in long16["rows"]),4),
         "historical_quality_36_categories":quality_categories,
         "production_quality_approved":False,"staged_inactive":True,
         "new_live_C09":atomic_live},
      "chimera":{"simulated_diagnostic_tools":"36/36 correct, 0 unsafe",
                 "current_8K":"3/3 full-prompt exact recall (last seed 8.48t/s)",
                 "current_16K":"failed watchdog during 6400-token prefill",
                 "production_agentic_general_approved":False},
      "gates":{"full_32K_64K_128K_real_GPU":"not validated",
               "agentic_JSON_code_real_quality":"unqualified",
               "live_Dify_n8n_Paperclip":"unqualified",
               "rollback_24h_canary":"not executed",
               "native_2_4_GPU_slots":"not proven"},
      "recommendation":"Do not promote either engine or edit stable OmniRoute combo until identical native C09+JSON/code, long-context and live-agent quality gates pass",
      "all_purpose_production_certified":False,
      "production_modified":False,
    }

if __name__=="__main__":
 print(json.dumps(decision(),ensure_ascii=False,indent=2))
