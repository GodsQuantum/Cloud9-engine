#!/usr/bin/env python3
"""Read-only audit of AutoPublisher's exported LLM nodes versus canonical prompts.

Never makes network/API calls, never executes a n8n workflow, never logs
raw prompts, transcript, credentials, body, or users' contact information.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

NODES = {
    "Editorial Extractor": "editorial_extractor_prompt.md",
    "Voice Copy Pack": "voice_copy_pack_prompt.md",
    "Repair Copy": "voice_copy_pack_prompt.md",
}
SYSTEM = re.compile(r"role:\s*'system',\s*content:\s*(\"(?:\\.|[^\"\\])*\")", re.S)
MODEL = re.compile(r"(?<![\w])model:\s*'([^']+)'")
TEMPERATURE = re.compile(r"(?<![\w])temperature:\s*(\d+(?:\.\d+)?)")
MAX_TOKENS = re.compile(r"(?<![\w])max_tokens:\s*(\d+)")
JSON_RESPONSE = re.compile(r"response_format:\s*\{\s*type:\s*'json_object'\s*\}")


def digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def inspect(workflow: dict, prompts_dir: Path) -> dict:
    if not isinstance(workflow, dict) or not isinstance(workflow.get("nodes"), list):
        raise ValueError("Expected a n8n workflow with nodes list")
    nodes = {}
    for node in workflow["nodes"]:
        name = node.get("name")
        if name in NODES:
            if name in nodes:
                raise ValueError(f"Duplicate LLM node {name}")
            nodes[name] = node
    missing = sorted(set(NODES) - set(nodes))
    if missing:
        raise ValueError("Missing required nodes: " + ", ".join(missing))
    reports = []
    for name, filename in NODES.items():
        node = nodes[name]
        params = node.get("parameters") or {}
        body = params.get("jsonBody")
        if not isinstance(body, str):
            raise ValueError(f"{name}: missing JSON body expression")
        match = SYSTEM.search(body)
        if not match:
            raise ValueError(f"{name}: no embedded system prompt literal")
        try:
            embedded = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{name}: malformed embedded system prompt") from exc
        target = (prompts_dir / filename).read_text(encoding="utf-8")
        refs = MODEL.findall(body)
        if len(refs) != 1:
            raise ValueError(f"{name}: expected exactly one explicit LLM alias")
        temp = TEMPERATURE.search(body)
        maximum = MAX_TOKENS.search(body)
        url = str(params.get("url") or "")
        parsed = urlparse(url)
        valid_transport = (
            node.get("type") == "n8n-nodes-base.httpRequest"
            and params.get("method") == "POST"
            and parsed.scheme in ("http", "https")
            and bool(parsed.hostname)
            and parsed.path.endswith("/v1/chat/completions")
            and params.get("specifyBody") == "json"
            and bool(params.get("sendBody"))
        )
        report = {
            "node": name,
            "model_alias": refs[0],
            "temperature": float(temp.group(1)) if temp else None,
            "max_tokens": int(maximum.group(1)) if maximum else None,
            "timeout_ms": (params.get("options") or {}).get("timeout"),
            "destination": f"{parsed.scheme}://{parsed.hostname}:{parsed.port or ('443' if parsed.scheme == 'https' else '80')}{parsed.path}" if parsed.hostname else "invalid",
            "prompt_sha256_embedded": digest(embedded),
            "prompt_sha256_current": digest(target),
            "prompt_matches_canonical": embedded == target,
            "json_object_response": bool(JSON_RESPONSE.search(body)),
            "valid_http_only": bool(valid_transport),
            "can_test_without_side_effects": True,
        }
        reports.append(report)
    return {
        "workflow_name": workflow.get("name"),
        "workflow_is_marked_active_in_export": workflow.get("active"),
        "workflow_version_id": workflow.get("versionId"),
        "source_is_file_snapshot_not_live_n8n_status": True,
        "llm_nodes": reports,
        "prompt_matches": all(x["prompt_matches_canonical"] for x in reports),
        "schema_transport_valid": all(x["json_object_response"] and x["valid_http_only"] and x["max_tokens"] for x in reports),
        "warning": "This is a read-only artifact comparison, not an LLM run or a deployed n8n verification.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", type=Path, required=True, help="Path to known n8n JSON export")
    parser.add_argument("--prompts", type=Path, required=True, help="Directory containing the two actual AutoPublisher prompts")
    parser.add_argument("--require-current-prompts", action="store_true", help="Exit nonzero if embedded prompt content has drifted")
    args = parser.parse_args()
    raw = json.loads(args.workflow.read_text(encoding="utf-8"))
    workflow = raw[0] if isinstance(raw, list) and len(raw) == 1 else raw
    try:
        report = inspect(workflow, args.prompts)
    except (ValueError, OSError, TypeError) as exc:
        print(json.dumps({"status": "invalid_snapshot", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["schema_transport_valid"]:
        return 4
    if args.require_current_prompts and not report["prompt_matches"]:
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
