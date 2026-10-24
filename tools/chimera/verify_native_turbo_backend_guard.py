#!/usr/bin/env python3
"""Strict source/policy guard gate for unpromoted Cloud9 MMB+MTP+TurboQuant."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MAN=ROOT/"tools/chimera/native-mmb-mtp-turbo-adaptive-backend-guard-20261024.json"

def git(src,*args):
    return subprocess.check_output(["git","-C",str(src),*args],text=True).strip()

def verify():
    m=json.loads(MAN.read_text())
    p=ROOT/m["port"]["patch"]
    assert m["kind"]=="LAB_NATIVE_CHIMERA_TURBO_BACKEND_FAIL_CLOSED_NOT_PRODUCTION"
    assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==m["port"]["patch_sha256"]
    assert m["qualification"]["production"] is False
    assert m["qualification"]["gpu_model_quality"] is False
    assert "ROCm" in m["added_policy"]["protects"]
    assert "Vulkan" in m["added_policy"]["keeps"]
    s=p.read_text()
    for mark in ("llama_cloud9_turbo_backend_allowed",
                 "ggml_backend_dev_backend_reg",
                 "ggml_backend_reg_name",
                 "Cloud9 TurboQuant K/V cache requires CPU or Vulkan",
                 "diff --git a/tests/test-cloud9-turbo-backend-policy.cpp",
                 "diff --git a/src/llama-cloud9-turbo-backend-policy.h",
                 "draft-mtp-adaptive", "GGML_CUDA_MMB"):
        assert mark in s,mark
    return m,p

def apply(src,m,p):
    assert git(src,"rev-parse","HEAD")==m["base"]["commit"]
    assert git(src,"rev-parse","HEAD^{tree}")==m["base"]["tree"]
    assert not git(src,"status","--porcelain")
    subprocess.run(["git","-C",str(src),"apply","--check",str(p)],check=True)
    subprocess.run(["git","-C",str(src),"apply",str(p)],check=True)
    subprocess.run(["git","-C",str(src),"add","-A"],check=True)
    assert not git(src,"diff","--cached","--check")
    actual=git(src,"write-tree")
    assert actual==m["port"]["resulting_tree"],(actual,m["port"]["resulting_tree"])
    print("TURBO_BACKEND_POLICY_EXACT_SOURCE_PASS",actual)

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--source",type=Path)
    a.add_argument("--apply",action="store_true")
    args=a.parse_args()
    m,p=verify()
    print("TURBO_FAIL_CLOSED_SOURCE_SHA_PASS",m["port"]["patch_sha256"])
    if args.apply:
        assert args.source
        apply(args.source,m,p)
