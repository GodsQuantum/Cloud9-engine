#!/usr/bin/env python3
"""Verify pinned source and combined MMB+MTP patch: no GPU claims."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tools/chimera/native-mmb-mtp-r120-on-master9ae-20261024.json"

def git(source, *args):
    return subprocess.check_output(["git", "-C", str(source), *args], text=True).strip()

def verify():
    m=json.loads(MANIFEST.read_text())
    p=ROOT / m["port"]["patch"]
    assert p.is_file()
    assert hashlib.sha256(p.read_bytes()).hexdigest()==m["port"]["patch_sha256"]
    d=p.read_text()
    for f in ("common/speculative.cpp", "src/llama-context.cpp", "src/llama-ext.h",
              "ggml/src/ggml-cuda/mmb.cu", "ggml/src/ggml-cuda/mmf32.cu"):
        assert "diff --git a/"+f in d, f
    assert "LLAMA_MTP_INGEST_TAIL" in d and "embd_nextn_from" in d
    assert m["qualification"]["production"] is False
    return m,p

def apply(source,m,p):
    assert git(source,"rev-parse","HEAD")==m["base"]["commit"]
    assert git(source,"rev-parse","HEAD^{tree}")==m["base"]["tree"]
    assert not git(source,"status","--porcelain")
    subprocess.run(["git","-C",str(source),"apply","--check",str(p)],check=True)
    subprocess.run(["git","-C",str(source),"apply",str(p)],check=True)
    subprocess.run(["git","-C",str(source),"add","-A"],check=True)
    assert not git(source,"diff","--cached","--check")
    tree=git(source,"write-tree")
    assert tree==m["port"]["resulting_tree"], (tree,m["port"]["resulting_tree"])
    print("CLOUD9_CHIMERA_EXACT_TREE_PASS",tree)

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--source",type=Path)
    a.add_argument("--apply",action="store_true")
    opts=a.parse_args()
    m,p=verify()
    print("CLOUD9_MERGED_NATIVE_PATCH_SHA_PASS",m["port"]["patch_sha256"])
    if opts.apply:
        assert opts.source
        apply(opts.source,m,p)
