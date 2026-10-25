#!/usr/bin/env python3
"""C10 read-only client concurrency LAB on an ALREADY loaded native CT410 worker.

No process spawning, GPU locks, service restarts, filesystem operations, or real tool execution.
One request per concurrent client, with official guardian and exact-model checks.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
from pathlib import Path
import socket
import statistics
import time
import urllib.request

from bench_native_agent_tools import fixture_list, toolbox, score

MODEL_ID = "Cloud9-Chimera-Qwen4-MTP-Vulkan-LAB"
PORT = 19755
BASE = "http://192.168.1.219:8090"
WORKER = "http://127.0.0.1:18091"
FIXTURE = "/srv/lxc/ia-compute/data/cloud9-engine-runtime/lab-releases/local-agent-readiness-20261024/infra_agentic_fixtures.json"


def fetch_json(url, body=None, timeout=5):
    raw = None if body is None else json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=raw, headers={"Content-Type": "application/json"} if raw else {})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def guardian_check(host="192.168.1.200"):
    with socket.create_connection((host, PORT), timeout=4) as conn:
        conn.settimeout(4)
        conn.sendall(b"CHECK coexist-light 0.00\n")
        return json.loads(conn.recv(16384).decode())


def p95(values):
    ordered = sorted(values)
    return round(ordered[math.ceil(0.95 * len(ordered)) - 1], 4) if ordered else None


def validate_slots(slots):
    if not isinstance(slots, list) or not slots:
        raise ValueError("LLAMA_NATIVE_SLOTS_MISSING")
    for slot in slots:
        if not isinstance(slot, dict):
            raise ValueError("INVALID_NATIVE_SLOT_RECORD")
    return len(slots)


def preflight(model, base, worker, guardian_host):
    if model != MODEL_ID:
        raise ValueError("ONLY_EXACT_CHIMERA_LAB_ALLOWED")
    h = fetch_json(base + "/health")
    if h.get("worker_model") != model:
        raise ValueError("EXACT_WORKER_NOT_ALREADY_LOADED: no implicit model start")
    g = guardian_check(guardian_host)
    if not g.get("allow"):
        raise ValueError("OFFICIAL_GUARDIAN_DENIED: " + repr(g.get("reasons")))
    slot_records = fetch_json(worker + "/slots", timeout=5)
    slots = validate_slots(slot_records)
    if any(x.get("is_processing") is True or x.get("state") == "processing" for x in slot_records):
        raise ValueError("NATIVE_WORKER_BUSY: do not disrupt clients")
    return {"worker_model": h["worker_model"], "native_slots": slots,
            "guardian": {k: g.get(k) for k in ("allow", "mem_available_gib", "psi_memory_full_avg10", "swap_used_percent", "reasons")}}


def tool_request(base, model, fixture, rep, client):
    payload = {"model": model, "temperature": 0, "seed": 8000 + rep * 10 + client,
        "stream": False, "parallel_tool_calls": False, "tool_choice": "required",
        "max_tokens": 140,
        "messages": [
            {"role": "system", "content": "Choisis exactement un outil de diagnostic en lecture seule. N'exécute aucun outil."},
            {"role": "user", "content": fixture["prompt_fr"]}],
        "tools": toolbox(fixture)}
    start = time.monotonic()
    reply = fetch_json(base + "/v1/chat/completions", payload, timeout=100)
    grade = score(reply, fixture)
    return {"phase": "tool", "rep": rep, "client": client, "fixture": fixture["id"],
        "wall_seconds": round(time.monotonic() - start, 4), **grade}


def stream_request(base, model, rep, client):
    payload = {"model": model, "temperature": 0, "seed": 9100 + rep * 10 + client,
        "stream": True, "max_tokens": 96,
        "messages": [{"role": "user", "content": "En trois phrases françaises courtes, décris une vérification de santé non destructive d'un service."}]}
    start = time.monotonic()
    events = []
    pieces = []
    raw = json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(base + "/v1/chat/completions", data=raw, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=95) as resp:
        while True:
            line = resp.readline()
            if not line:
                break
            line = line.decode("utf-8", "replace").strip()
            if not line.startswith("data: "):
                continue
            data = line[6:].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            choice = (chunk.get("choices") or [{}])[0]
            delta = (choice.get("delta") or {}).get("content")
            if isinstance(delta, str) and delta:
                events.append(time.monotonic() - start)
                pieces.append(delta)
    total = round(time.monotonic() - start, 4)
    return {"phase": "stream", "rep": rep, "client": client,
        "passed": bool("".join(pieces).strip()), "wall_seconds": total,
        "ttft_seconds": round(events[0], 4) if events else None,
        # SSE fragments are NOT guaranteed to map to individual tokens.
        "inter_chunk_seconds": [round(b - a, 4) for a, b in zip(events, events[1:])],
        "chunks": len(events),
        "text_sha256": hashlib.sha256("".join(pieces).encode()).hexdigest()}


def summarize(rows, slots):
    tool = [x for x in rows if x.get("phase") == "tool"]
    stream = [x for x in rows if x.get("phase") == "stream"]
    all_ttft = [r["ttft_seconds"] for r in stream if r.get("ttft_seconds") is not None]
    delays = [v for x in stream for v in x.get("inter_chunk_seconds", [])]
    return {"requests": len(rows), "passed": sum(bool(x.get("passed")) for x in rows),
        "tool_requests": len(tool), "tool_correct": sum(bool(x.get("passed")) for x in tool),
        "unsafe_tool_calls": sum(bool(x.get("unsafe")) for x in tool),
        "native_decoding_slots": slots,
        "server_true_parallelism_proven": False,
        "p95_total_seconds": p95([x["wall_seconds"] for x in rows if "wall_seconds" in x]),
        "p95_stream_ttft_seconds": p95(all_ttft),
        "p95_inter_chunk_seconds": p95(delays),
        "inter_chunk_is_not_exact_itl": True}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="Only with exact LAB worker already loaded")
    ap.add_argument("--model", default=MODEL_ID)
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--worker", default=WORKER)
    ap.add_argument("--guardian-host", default="192.168.1.200")
    ap.add_argument("--fixture", default=FIXTURE)
    ap.add_argument("--repetitions", type=int, default=3)
    ap.add_argument("--output")
    a = ap.parse_args(argv)
    if a.repetitions != 3:
        ap.error("C10 qualification requires three repetitions")
    fixture_file = Path(a.fixture)
    if not a.execute:
        print(json.dumps({"status": "dry_run_only", "model": a.model, "clients": [1, 2, 4],
                          "repetitions": 3, "native_worker_must_preexist": True,
                          "tool_calls_simulated": True, "production_untouched": True}))
        return
    if not a.output:
        ap.error("--output is mandatory for --execute")
    out = Path(a.output)
    if out.exists():
        ap.error("IMMUTABLE_EVIDENCE_COLLISION; supply a fresh --output")
    if a.model != MODEL_ID:
        ap.error("ONLY_EXACT_CHIMERA_LAB_ALLOWED")
    fixtures = fixture_list(fixture_file)
    pilot = preflight(a.model, a.base, a.worker, a.guardian_host)
    report = {"status": "running", "model": a.model, "lab_only": True,
        "safe_simulated_tools": True, "no_worker_load_or_preemption": True,
        "fixture_sha256": hashlib.sha256(fixture_file.read_bytes()).hexdigest(),
        "baseline": pilot, "native_slots": pilot["native_slots"], "rows": []}
    def save():
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    save()
    try:
        for phase in ("tool", "stream"):
            for clients in (1, 2, 4):
                for rep in range(1, 4):
                    current = preflight(a.model, a.base, a.worker, a.guardian_host)
                    if current["native_slots"] != pilot["native_slots"]:
                        raise RuntimeError("NATIVE_SLOT_COUNT_CHANGED")
                    with ThreadPoolExecutor(max_workers=clients) as pool:
                        futures = []
                        for client in range(clients):
                            if phase == "tool":
                                fixture = fixtures[(rep * 4 + client) % len(fixtures)]
                                futures.append(pool.submit(tool_request, a.base, a.model, fixture, rep, client))
                            else:
                                futures.append(pool.submit(stream_request, a.base, a.model, rep, client))
                        for future in as_completed(futures):
                            row = future.result()
                            row["client_concurrency"] = clients
                            report["rows"].append(row)
                            save()
                            if not row.get("passed") or row.get("unsafe"):
                                raise RuntimeError("QUALITY_OR_SAFETY_FAILURE")
                    h = fetch_json(a.base + "/health")
                    if h.get("worker_model") != a.model:
                        raise RuntimeError("WORKER_EVICTED_DURING_BENCHMARK")
        report["status"] = "complete_client_concurrency"
        if pilot["native_slots"] < 4:
            report["status"] = "client_queue_measured_native_4slots_not_proven"
    except Exception as exc:
        report["status"] = "paused_or_failed"
        report["stop_reason"] = type(exc).__name__ + ": " + str(exc)[:280]
    finally:
        report["scorecard"] = summarize(report["rows"], pilot["native_slots"])
        save()
        print("C10_RESULT", json.dumps({"status": report["status"],
            "native_slots": pilot["native_slots"], **report["scorecard"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
