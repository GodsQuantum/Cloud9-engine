#!/usr/bin/env python3
"""Rank engine/model pairs only from measured evidence; no GPU/service actions."""
import argparse
import json
import math
from pathlib import Path

REQUIRED = ("json", "tools", "code", "fr")
FLOOR = {"json": 1.0, "tools": 1.0, "code": .8, "fr": .75}

def evaluate(item):
    issues = []
    ident = item.get("identity", {})
    for n in ("engine", "model", "quant", "model_sha256", "engine_sha256"):
        if not ident.get(n):
            issues.append("missing identity." + n)
    for n in ("model_sha256", "engine_sha256"):
        s = ident.get(n, "")
        if len(s) != 64 or any(x not in "0123456789abcdef" for x in s):
            issues.append("invalid SHA256 " + n)
    spec = item.get("speculation", {})
    if not spec.get("native_supported") or not spec.get("enabled"):
        issues.append("MTP/native speculation not active")
    if spec.get("draft_accepted", 0) < 1 or spec.get("draft_proposed", 0) < spec.get("draft_accepted", 0):
        issues.append("no verified accepted draft tokens")
    if item.get("repetitions", 0) < 3:
        issues.append("less than 3 real trials")
    if item.get("hardware") != "Cloud9 Radeon 780M gfx1103":
        issues.append("not measured on Cloud9")
    correctness = item.get("quality", {})
    grades = []
    for k in REQUIRED:
        v = correctness.get(k, {})
        n, ok = v.get("n", 0), v.get("correct", -1)
        if not isinstance(n, int) or n < 3 or not isinstance(ok, int) or not 0 <= ok <= n:
            issues.append("insufficient quality evidence: " + k)
        else:
            grades.append(ok / n)
            if ok / n < FLOOR[k]:
                issues.append("quality below floor: " + k)
    eligible_context = []
    for e in item.get("context", []):
        n, attempts, ok, positions = (e.get("observed_prompt_tokens", 0), e.get("retrieval_trials", 0),
                                     e.get("retrieval_correct", 0), e.get("positions", 0))
        if n >= 8192 and attempts >= 5 and ok <= attempts and ok / attempts >= .9 and positions >= 5 and e.get("no_truncation_proven") is True:
            eligible_context.append(n)
    verified_ctx = max(eligible_context, default=0)
    if not verified_ctx:
        issues.append("no real, untruncated multi-position effective context")
    perf = item.get("performance", {})
    for k in ("decode_tps", "prefill_tps", "time_to_correct_tool_s"):
        v = perf.get(k, 0)
        if not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
            issues.append("missing measured performance: " + k)
    safety = item.get("safety", {})
    if safety.get("device_lost") is not False or safety.get("oom") is not False or safety.get("service_regression") is not False:
        issues.append("resource/service safety not proven")
    t = safety.get("peak_tctl_c", 99)
    if not isinstance(t, (int, float)) or not 0 < t < 78:
        issues.append("thermal margin not proven")
    mem = safety.get("peak_host_ram_gib", 0)
    if not isinstance(mem, (int, float)) or mem <= 0:
        issues.append("RAM use not recorded")
    if item.get("openai_native_tools_ok") is not True:
        issues.append("native tools API missing")
    return {"id": ident.get("id", ident.get("engine", "?") + "/" + ident.get("model", "?")),
            "eligible": not issues, "issues": issues,
            "quality": sum(grades) / 4 if len(grades) == 4 else None,
            "context": verified_ctx, "decode": perf.get("decode_tps"),
            "prefill": perf.get("prefill_tps"), "tool_latency": perf.get("time_to_correct_tool_s"),
            "ram": mem}

def dominates(a, b):
    hi = ("quality", "context", "decode", "prefill")
    lo = ("tool_latency", "ram")
    return (all(a[k] >= b[k] for k in hi) and all(a[k] <= b[k] for k in lo) and
            (any(a[k] > b[k] for k in hi) or any(a[k] < b[k] for k in lo)))

def rank(data):
    if data.get("schema_version") != 1 or not isinstance(data.get("candidates"), list):
        raise ValueError("expected version 1, list of candidates")
    items = [evaluate(c) for c in data["candidates"]]
    passing = [x for x in items if x["eligible"]]
    pareto = [a["id"] for a in passing if not any(dominates(b,a) for b in passing if b is not a)]
    return {"status": "UNPROVEN" if len(passing)<2 else "PARETO_REVIEW_NOT_PRODUCTION",
            "eligible":len(passing), "total":len(items), "pareto":pareto, "items":items}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("evidence",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    summary=rank(json.loads(args.evidence.read_text(encoding="utf8")))
    output=json.dumps(summary,ensure_ascii=False,indent=2)+"\n"
    if args.output: args.output.write_text(output,encoding="utf8")
    else: print(output,end="")
    raise SystemExit(0 if summary["eligible"]>=2 else 2)
