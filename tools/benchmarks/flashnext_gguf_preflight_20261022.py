#!/usr/bin/env python3
"""Low-I/O GGUF family/format preflight for Cloud9's single-engine tournament.

Reads ONLY GGUF metadata, not large tensor payloads; changes no files.
Does NOT claim GPU compatibility, token generation, MTP correctness or throughput.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import struct

SIZES = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4,
         7: 1, 10: 8, 11: 8, 12: 8}
FMT = {0: "B", 1: "b", 2: "H", 3: "h", 4: "I", 5: "i", 6: "f",
       7: "?", 10: "Q", 11: "q", 12: "d"}
MAX_STRING = 16 * 1024 * 1024
MAX_META_ENTRIES = 100_000
MAX_ARRAY_ITEMS = 3_000_000
MAX_HEADER_READ = 80 * 1024 * 1024

class GGUFError(ValueError):
    """Refuse partial/corrupt/incompatible metadata."""

class Cursor:
    def __init__(self, path: Path):
        self.path = path
        self.file = path.open("rb")

    def close(self):
        self.file.close()

    def get(self, count: int) -> bytes:
        if count < 0 or self.file.tell() + count > MAX_HEADER_READ:
            raise GGUFError("metadata cap exceeded")
        b = self.file.read(count)
        if len(b) != count:
            raise GGUFError("truncated GGUF metadata")
        return b

    def integer(self, code="Q"):
        return struct.unpack("<" + code, self.get(struct.calcsize(code)))[0]

    def string(self):
        n = self.integer()
        if n > MAX_STRING:
            raise GGUFError(f"unreasonably long metadata string: {n}")
        return self.get(n).decode("utf-8")

    def value(self, typ: int, keep=True):
        if typ == 8:
            if keep:
                return self.string()
            n = self.integer()
            if n > MAX_STRING:
                raise GGUFError("string exceeds limit")
            self.get(n)
            return None
        if typ in FMT:
            x = self.integer(FMT[typ])
            return x if keep else None
        if typ == 9:
            elem, count = self.integer("I"), self.integer()
            if count > MAX_ARRAY_ITEMS:
                raise GGUFError("array exceeds limit")
            if elem in SIZES:
                self.get(count * SIZES[elem])
            elif elem == 8:
                for _ in range(count):
                    self.value(8, keep=False)
            else:
                raise GGUFError(f"unsupported array type: {elem}")
            return f"<array {count} of {elem}>" if keep else None
        raise GGUFError(f"unsupported GGUF metadata type: {typ}")

def parse_metadata(path: Path) -> dict:
    if not path.is_file():
        raise GGUFError(f"file absent: {path}")
    c = Cursor(path)
    try:
        if c.get(4) != b"GGUF":
            raise GGUFError("not GGUF")
        version = c.integer("I")
        if version not in (2, 3):
            raise GGUFError(f"unsupported GGUF version {version}")
        tensors, entries = c.integer(), c.integer()
        if entries > MAX_META_ENTRIES:
            raise GGUFError("too many metadata entries")
        wanted = {"general.architecture", "general.name", "general.file_type",
                  "split.count", "split.no", "split.tensors.count",
                  "tokenizer.ggml.model"}
        result = {}
        for _ in range(entries):
            key = c.string()
            typ = c.integer("I")
            retain = (key in wanted or key.endswith(".context_length") or
                      key.endswith(".nextn_predict_layers") or
                      key.endswith(".attention.head_count") or
                      key.endswith(".expert_count") or
                      key.endswith(".expert_used_count"))
            val = c.value(typ, keep=retain)
            if retain:
                result[key] = val
        return {"path": str(path), "bytes": path.stat().st_size,
                "gguf_version": version, "tensor_count": tensors,
                "metadata_entries": entries, "selected_metadata": result,
                "metadata_end_offset": c.file.tell()}
    finally:
        c.close()

def validate_split_group(paths: list[Path]) -> dict:
    if not paths:
        raise GGUFError("no model files")
    names = [p.name for p in paths]
    if len(set(names)) != len(names):
        raise GGUFError("duplicate shard")
    patterns = [re.search(r"-(\d{5})-of-(\d{5})\.gguf$", name) for name in names]
    if len(paths) > 1 or any(m is not None for m in patterns):
        if any(m is None for m in patterns):
            raise GGUFError("split GGUF names must use NNNNN-of-NNNNN")
        declared = {int(m.group(2)) for m in patterns}
        if declared != {len(paths)}:
            raise GGUFError("missing/inconsistent shards")
        if {int(m.group(1)) for m in patterns} != set(range(1, len(paths)+1)):
            raise GGUFError("non-contiguous shard indices")
    records = [parse_metadata(p) for p in paths]
    declared_counts = {r["selected_metadata"].get("split.count")
                       for r in records if "split.count" in r["selected_metadata"]}
    declared_tensors = {r["selected_metadata"].get("split.tensors.count")
                        for r in records if "split.tensors.count" in r["selected_metadata"]}
    if declared_counts and declared_counts != {len(records)}:
        raise GGUFError("GGUF header split.count differs from filenames")
    if declared_tensors and declared_tensors != {sum(r["tensor_count"] for r in records)}:
        raise GGUFError("GGUF shard tensor totals disagree")
    architectures = {r["selected_metadata"].get("general.architecture")
                     for r in records if "general.architecture" in r["selected_metadata"]}
    if len(architectures) > 1:
        raise GGUFError(f"mixed model architectures: {architectures}")
    keys = {}
    for r in records:
        keys.update(r["selected_metadata"])
    return {"status": "metadata_only_not_gpu_certified",
            "shards": len(records), "total_bytes": sum(r["bytes"] for r in records),
            "architecture": next(iter(architectures), None),
            "context_metadata": {k: v for k, v in keys.items() if "context_length" in k},
            "mtp_metadata": {k: v for k, v in keys.items() if "nextn_predict_layers" in k},
            "expert_metadata": {k: v for k, v in keys.items() if "expert_count" in k},
            "parts": records,
            "warnings": ["Model metadata and file presence are not proof of native MTP, useful long context, valid token generation or performance."]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("gguf", type=Path, nargs="+")
    p.add_argument("--expected-architecture", choices=["qwen4exp", "qwen35moe", "qwen35"])
    args = p.parse_args()
    out = validate_split_group(args.gguf)
    if args.expected_architecture and out["architecture"] != args.expected_architecture:
        raise SystemExit(f"Architecture mismatch: got {out['architecture']}")
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
