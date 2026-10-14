#!/usr/bin/env python3
"""Fail-closed AI-runtime benchmark candidate gate (read-only; no GPU or network).

Compare *only* same audio/text fixture, provenance of base weights and quant
scheme, and protocol. A source compilation is NOT an inference benchmark.
This CLI never promotes any runtime, writes a file, or queries a model.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import median


METRICS = {
    "decode_tps": "higher",
    "prefill_tps": "higher",
    "wall_s": "lower",
    "quality_score": "higher",
    "peak_gtt_bytes": "lower",
}
SPEED_KEYS = ("decode_tps", "prefill_tps", "wall_s")
GATE_REPEATS = 3
DEFAULT_RELATIVE_TOLERANCE = 0.05
MAX_QUALITY_DROP_POINTS = 2.0
MODEL_REQUIRED = ("base_weights_fingerprint", "quantization_scheme")
CONTEXT_REQUIRED = ("benchmark_protocol_id", "fixture_sha256", "context_tokens")


def finite_number(v):
    return type(v) in (float, int) and math.isfinite(v)


def stable_identity(record):
    config = record.get("configuration") or {}
    ctx = record.get("context") or {}
    return {key: config.get(key) for key in MODEL_REQUIRED} | {
        key: ctx.get(key) for key in CONTEXT_REQUIRED
    }


def complete_identity(record):
    identity = stable_identity(record)
    missing = [key for key, value in identity.items()
               if value is None or value == "" or (key != "context_tokens" and not isinstance(value, str))]
    if missing:
        return False, "Missing fingerprint/protocol metadata: " + ", ".join(missing)
    if type(identity["context_tokens"]) is not int or identity["context_tokens"] <= 0:
        return False, "Invalid context_tokens"
    for name in ("base_weights_fingerprint", "fixture_sha256"):
        h = identity[name]
        if len(h) != 64 or any(c not in "0123456789abcdef" for c in h.lower()):
            return False, f"{name} must be the original 64-hex SHA256"
    return True, ""


def run_stats(record):
    runs = (record.get("metrics") or {}).get("repeated_runs")
    if not isinstance(runs, list) or len(runs) < GATE_REPEATS:
        return None, "Need >=3 independent recorded inference runs"
    values = {key: [] for key in METRICS}
    for i, run in enumerate(runs):
        if not isinstance(run, dict) or run.get("status") != "ok":
            return None, f"Run {i + 1} is incomplete or failed"
        for key in METRICS:
            v = run.get(key)
            if not finite_number(v) or v < 0 or (key in SPEED_KEYS and v == 0):
                return None, f"Run {i + 1} invalid/missing {key}"
            if key == "quality_score" and v > 100:
                return None, f"Run {i + 1} quality_score out of range"
            values[key].append(float(v))
    return {key: median(vals) for key, vals in values.items()}, ""


def compare(candidate, baseline_records, tolerance=DEFAULT_RELATIVE_TOLERANCE):
    """Return structured evidence. 0=eligible, 2=regression, 3=incomparable."""
    report = {
        "candidate_id": candidate.get("id"),
        "candidate_engine": (candidate.get("engine_identity") or {}).get("family")
                            or candidate.get("engine"),
        "status": "incomparable",
        "eligible_for_promotion": False,
        "new_runtime_was_executed_by_this_tool": False,
        "reference_id": None,
        "differences": {},
        "issues": [],
    }
    if candidate.get("validation") != "validated_in_source":
        report["issues"].append("Candidate is not a validated on-machine run")
        return 3, report
    ok, reason = complete_identity(candidate)
    if not ok:
        report["issues"].append(reason)
        return 3, report
    if not 0 <= tolerance <= 0.5:
        report["issues"].append("Invalid relative tolerance")
        return 3, report
    cand_stats, reason = run_stats(candidate)
    if cand_stats is None:
        report["issues"].append(reason)
        return 3, report
    identity = stable_identity(candidate)
    matches = [r for r in baseline_records
               if r.get("id") != candidate.get("id")
               and r.get("validation") == "validated_in_source"
               and stable_identity(r) == identity]
    # For cross-engine comparisons, matching base weights and quantification
    # must be *explicit*. Different GGUF/Strata pack files may encode different
    # arithmetic; callers cannot infer identical weights from a shared model name.
    accepted_baselines = []
    for r in matches:
        baseline_stats, problem = run_stats(r)
        if baseline_stats is not None:
            accepted_baselines.append((r, baseline_stats))
    if not accepted_baselines:
        report["issues"].append(
            "No source-validated baseline with identical base-weights SHA256, quantization "
            "scheme, context, fixture SHA256 and protocol, >=3 good recorded runs. "
            "Older Hall of Fame speed-only records cannot certify a promotion."
        )
        return 3, report
    # Select the baseline with the best wall latency among independently measured
    # same-input and quality-qualified records; never cherry-pick only the slowest
    # older run to manufacture a win.
    ref, baseline = min(
        accepted_baselines, key=lambda r: (r[1]["wall_s"], -r[1]["quality_score"])
    )
    report["reference_id"] = ref["id"]
    failures = []
    for key in METRICS:
        old = baseline[key]
        new = cand_stats[key]
        if key == "quality_score":
            pass_gate = new >= old - MAX_QUALITY_DROP_POINTS
        elif old == 0:
            pass_gate = new == 0
        elif METRICS[key] == "higher":
            pass_gate = new >= old * (1 - tolerance)
        else:
            pass_gate = new <= old * (1 + tolerance)
        delta = None if old == 0 else round((new / old - 1) * 100, 3)
        report["differences"][key] = {
            "baseline_median": old,
            "candidate_median": new,
            "relative_change_pct": delta,
            "direction": METRICS[key],
            "gate_pass": bool(pass_gate),
        }
        if not pass_gate:
            failures.append(f"{key} regression beyond allowed tolerance")
    report["issues"] = failures
    if failures:
        report["status"] = "regression"
        return 2, report
    report["status"] = "eligible_for_separate_hardware_and_agent_gates"
    report["eligible_for_promotion"] = False
    report["issues"] = [
        "Numeric benchmark parity passed; still require real GPU stability, "
        "VRAM/UMA service coexistence, complete model quality and actual "
        "AutoPublisher/Archie workflow correctness before promotion."
    ]
    return 0, report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hall", type=Path, required=True, help="Existing ONE Hall of Fame JSON")
    ap.add_argument("--candidate", type=Path, required=True, help="One proposed JSON benchmark record")
    ap.add_argument("--relative-tolerance", type=float, default=DEFAULT_RELATIVE_TOLERANCE)
    opts = ap.parse_args()
    try:
        hall = json.loads(opts.hall.read_text())
        candidate = json.loads(opts.candidate.read_text())
        if not isinstance(hall, dict) or not isinstance(hall.get("records"), list):
            raise ValueError("Not an existing Hall of Fame")
        if not isinstance(candidate, dict):
            raise ValueError("Candidate record must be an object")
        code, report = compare(candidate, hall["records"], opts.relative_tolerance)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "invalid_input", "reason": str(exc)}))
        return 4
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
