#!/usr/bin/env python3
"""Read-only GGUF capability / theoretical KV sizing. Never launches GPU."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct

GGUF_MODEL = Path("/srv/lxc/ia-compute/data/models/bakeoff-20261002/qwen38distill-qwen35-4b-mtp/Qwen3.5-4B-Qwen3.8-Distill-Heretic-MTP-Q4_K_M.gguf")
TYPES = {0:"B",1:"b",2:"H",3:"h",4:"I",5:"i",6:"f",7:"?",10:"Q",11:"q",12:"d"}
TIER = (8192, 16384, 32768, 65536, 131072, 262144)

def metadata(path):
    """Read GGUF header and metadata only; never read tensor weights."""
    with Path(path).open("rb") as f:
        def read(n):
            b=f.read(n)
            if len(b)!=n:raise ValueError("GGUF_TRUNCATED")
            return b
        def val(kind, keep=True):
            if kind==8:
                n=struct.unpack("<Q",read(8))[0]
                if n>8_000_000:raise ValueError("GGUF_METADATA_STRING_TOO_LONG")
                if not keep:f.seek(n,1);return None
                return read(n).decode("utf-8","replace")
            if kind==9:
                subtype=struct.unpack("<I",read(4))[0]
                n=struct.unpack("<Q",read(8))[0]
                if n>2_000_000:raise ValueError("GGUF_ARRAY_TOO_LONG")
                if subtype in TYPES:
                    size=struct.calcsize(TYPES[subtype])
                    if n>128 or not keep:
                        f.seek(n*size,1)
                        return {"array_length":n}
                if n>128 or not keep:
                    for _ in range(n):val(subtype,False)
                    return {"array_length":n}
                return [val(subtype) for _ in range(n)]
            if kind not in TYPES:raise ValueError("GGUF_UNKNOWN_TYPE")
            return struct.unpack("<"+TYPES[kind],read(struct.calcsize(TYPES[kind])))[0]
        if read(4)!=b"GGUF":raise ValueError("INVALID_GGUF")
        version, n_tensors, n_kv=struct.unpack("<IQQ",read(20))
        if version!=3 or n_kv>100_000:raise ValueError("UNSUPPORTED_GGUF")
        result={"version":version,"tensor_count":n_tensors}
        keys={"general.architecture","general.name",
              "qwen35.context_length","qwen35.block_count",
              "qwen35.attention.head_count_kv","qwen35.attention.key_length",
              "qwen35.attention.value_length","qwen35.full_attention_interval"}
        for _ in range(n_kv):
            key=val(8)
            t=struct.unpack("<I",read(4))[0]
            value=val(t, key in keys)
            if key in keys:result[key]=value
        return result

def estimate(meta, n_tokens):
    assert n_tokens>0
    if meta["general.architecture"]!="qwen35":
        raise ValueError("ONLY_QWEN35_HYBRID_SUPPORTED")
    # ATTENTION: ceil approximation of full attention layers. For 33 blocks
    # 33 may contain an auxiliary MTP layer; therefore these values are
    # planning estimates, NOT native llama.cpp allocations.
    blocks=int(meta["qwen35.block_count"])
    interval=int(meta["qwen35.full_attention_interval"])
    layers=(blocks+interval-1)//interval
    heads=int(meta["qwen35.attention.head_count_kv"])
    n_k=int(meta["qwen35.attention.key_length"])
    n_v=int(meta["qwen35.attention.value_length"])
    floats_per_token=layers*heads*(n_k+n_v)
    # GGML q8_0 quantization: 32 int8 values + 2-byte f16 scale =34 bytes.
    def q8_bytes(width):return ((width+31)//32)*34
    f16_bytes_per_token=floats_per_token*2
    q8_bytes_per_token=layers*heads*(q8_bytes(n_k)+q8_bytes(n_v))
    return {"tokens":n_tokens,"assumed_full_attention_layers":layers,
            "estimated_KV_f16_GiB":round(n_tokens*f16_bytes_per_token/2**30,3),
            "estimated_KV_q8_0_GiB":round(n_tokens*q8_bytes_per_token/2**30,3),
            "not_included":"weights, Mamba/SSM state, compute buffers, Vulkan scratch, runtime, prompt or host/system RAM",
            "evidence_class":"THEORETICAL_APPROXIMATION_NOT_GPU_CERTIFICATION"}

def report(path):
    m=metadata(path)
    assert m["qwen35.context_length"]>=262144
    return {"model_metadata":m,"source_file_bytes":Path(path).stat().st_size,
            "native_supported_context_tokens":int(m["qwen35.context_length"]),
            "context_envelope":[estimate(m,x) for x in TIER],
            "policy":{"routine_prompt":"8K-32K after proven admission",
                      "large_single_task":"64K after 5-marker full-inference certification",
                      "agentic_target":"128K with retrieval/memory, capacity and latency proofs required",
                      "architecture_max":"262K advertised GGUF metadata; not a measured usable window",
                      "guard":"must keep official GPU coexistence and model-specific admission thresholds",
                      "production_promoted":False,
                      "full_inference_above_8k_certified":False}}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--gguf",type=Path,default=GGUF_MODEL)
    args=parser.parse_args()
    print(json.dumps(report(args.gguf),ensure_ascii=False,indent=2))
