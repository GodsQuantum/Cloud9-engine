#!/usr/bin/env python3
"""Fail-closed KV codec qualification. No inference, filesystem writes or implicit deployment."""
from __future__ import annotations
import argparse, json, statistics as stats
from pathlib import Path

CASES=("retrieval","calendar")
MIN_CONTEXT=32768
MIN_LONG_PROMPT=8192
MIN_MEMORY_SAVING=0.20
MAX_LONG_WALL_RATIO=1.05
MAX_TOOL_WALL_RATIO=1.15
MIN_REPEATS=3

def _rows(variant,case):
    return [r for r in variant.get("rows",[]) if r.get("case")==case]

def _median_wall(variant,case):
    return stats.median(float(r["wall_s"]) for r in _rows(variant,case))

def judge(payload,candidate):
    reasons=[]
    variants=payload.get("comparisons",{})
    baseline=variants.get("f16")
    trial=variants.get(candidate)
    if payload.get("context")!=MIN_CONTEXT:reasons.append("context_mismatch")
    if not baseline or not trial:
        return {"eligible":False,"candidate":candidate,"reasons":["missing_baseline_or_trial"]}
    if trial.get("K") not in ("q8_0","f16") or trial.get("V") not in ("turbo4","turbo3"):
        reasons.append("unsupported_kv_combination")
    for label,row in (("f16",baseline),(candidate,trial)):
        if row.get("status")!="passed":reasons.append(label+"_status_unvalidated")
        for case in CASES:
            vals=_rows(row,case)
            if len(vals)<MIN_REPEATS:reasons.append(label+"_"+case+"_insufficient_repeats")
            if not all(r.get("correct") is True for r in vals):reasons.append(label+"_"+case+"_quality_regression")
        lengths=[x.get("prompt_tokens") for x in _rows(row,"retrieval")]
        if not lengths or not all(isinstance(t,int) and t>=MIN_LONG_PROMPT for t in lengths):
            reasons.append(label+"_long_context_not_measured")
    if not reasons:
        if _median_wall(trial,"retrieval")>_median_wall(baseline,"retrieval")*MAX_LONG_WALL_RATIO:
            reasons.append("long_prompt_latency_regressed")
        if _median_wall(trial,"calendar")>_median_wall(baseline,"calendar")*MAX_TOOL_WALL_RATIO:
            reasons.append("tool_latency_regressed")
    # RSS is not KV allocation and systemwide GTT counts other processes.
    # Require isolated per-model KV memory measurements before a memory promotion.
    old=baseline.get("isolated_kv_allocation_mib")
    new=trial.get("isolated_kv_allocation_mib")
    if not isinstance(old,(int,float)) or not isinstance(new,(int,float)) or new<=0 or old<=0:
        reasons.append("isolated_kv_memory_evidence_missing")
    elif (old-new)/old<MIN_MEMORY_SAVING:
        reasons.append("measured_kv_saving_below_20_percent")
    return {"eligible":not reasons,"candidate":candidate,"reasons":sorted(set(reasons)),
            "minimum_context":MIN_CONTEXT,"minimum_repeats":MIN_REPEATS}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("evidence",type=Path)
    ap.add_argument("--candidate",choices=["q8k-turbo3v","q8k-turbo4v"],required=True)
    ap.add_argument("--json",action="store_true")
    args=ap.parse_args()
    result=judge(json.loads(args.evidence.read_text()),args.candidate)
    print(json.dumps(result,indent=2,sort_keys=True) if args.json else ("ELIGIBLE" if result["eligible"] else "NOT ELIGIBLE: "+", ".join(result["reasons"])))
    raise SystemExit(0 if result["eligible"] else 2)

if __name__=="__main__":main()
