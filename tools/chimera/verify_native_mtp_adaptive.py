#!/usr/bin/env python3
"""Apply SHA-pinned experimental native Cloud9 Turbo+MTP-adaptive patch to exact base."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MAN=ROOT/"tools/chimera/native-mmb-mtp-turbo-adaptive-master9ae-20261024.json"

def g(src,*a):
 return subprocess.check_output(["git","-C",str(src),*a],text=True).strip()

def verify():
 m=json.loads(MAN.read_text())
 p=ROOT/m["port"]["patch"]
 assert m["kind"]=="LAB_NATIVE_CHIMERA_MTP_ADAPTIVE_EXPERIMENTAL_NOT_PRODUCTION"
 assert p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==m["port"]["patch_sha256"]
 blob=p.read_text()
 for marker in ("diff --git a/common/speculative-adaptive.h",
                "diff --git a/common/speculative.cpp",
                "diff --git a/ggml/src/ggml-cuda/mmb.cu",
                "diff --git a/tests/test-speculative-adaptive.cpp",
                "--spec-draft-n-min-adaptive", "--spec-draft-n-start",
                "LLAMA_MTP_TAIL_READBACK"):
  assert marker in blob,marker
 for f in ("vulkan_compile","hip_compile","gpu_execution","agentic_quality","production"):
  assert m["qualification"][f] is False,f
 return m,p

def apply(src,m,p):
 assert g(src,"rev-parse","HEAD")==m["source_upstream"]["commit"]
 assert g(src,"rev-parse","HEAD^{tree}")==m["source_upstream"]["tree"]
 assert not g(src,"status","--porcelain")
 subprocess.run(["git","-C",str(src),"apply","--check",str(p)],check=True)
 subprocess.run(["git","-C",str(src),"apply",str(p)],check=True)
 subprocess.run(["git","-C",str(src),"add","-A"],check=True)
 assert not g(src,"diff","--cached","--check")
 actual=g(src,"write-tree")
 assert actual==m["port"]["resulting_tree"],(actual,m["port"]["resulting_tree"])
 print("ADAPTIVE_PORT_EXACT_TREE_PASS",actual)

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--source",type=Path)
 parser.add_argument("--apply",action="store_true")
 a=parser.parse_args()
 m,p=verify()
 print("ADAPTIVE_PATCH_SHA_PASS",m["port"]["patch_sha256"])
 if a.apply:
  assert a.source
  apply(a.source,m,p)
