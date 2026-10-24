#!/usr/bin/env python3
"""Strict source reconstruction for combined native Cloud9 MMB+MTP+TurboQuant candidate."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MAN=ROOT/"tools/chimera/native-mmb-mtp-turbo-on-master9ae-20261024.json"

def git(s,*arg):
 return subprocess.check_output(["git","-C",str(s),*arg],text=True).strip()

def load():
 m=json.loads(MAN.read_text())
 assert m["kind"]=="LAB_SOURCE_CHIMERA_MMB_MTP_TURBOQUANT_VULKAN_NOT_PRODUCTION"
 p=ROOT/m["port"]["patch"]
 assert p.is_file()
 assert hashlib.sha256(p.read_bytes()).hexdigest()==m["port"]["patch_sha256"]
 data=p.read_text()
 for name in ("ggml/src/ggml-turbo-quant.c","ggml/include/ggml.h",
              "ggml/src/ggml-vulkan/ggml-vulkan.cpp","ggml/src/ggml-vulkan/vulkan-shaders/flash_attn_dequant.glsl",
              "ggml/src/ggml-cuda/mmb.cu", "src/llama-context.cpp", "src/llama-graph.cpp"):
  assert "diff --git a/"+name in data, name
 for term in ("GGML_TYPE_TURBO3_0","GGML_TYPE_TURBO4_0","LLAMA_MTP_INGEST_TAIL",
              "GGML_CUDA_MMB","llama_turbo_wht"):
  assert term in data,term
 assert m["qualification"]["production"] is False
 assert len(m["donor_atomic_patches"])==8
 return m,p

def apply_to(src,m,p):
 assert git(src,"rev-parse","HEAD")==m["base"]["commit"]
 assert git(src,"rev-parse","HEAD^{tree}")==m["base"]["tree"]
 assert not git(src,"status","--porcelain")
 subprocess.run(["git","-C",str(src),"apply","--check",str(p)],check=True)
 subprocess.run(["git","-C",str(src),"apply",str(p)],check=True)
 subprocess.run(["git","-C",str(src),"add","-A"],check=True)
 assert not git(src,"diff","--cached","--check")
 assert git(src,"write-tree")==m["port"]["resulting_tree"]
 print("COMBINED_NATIVE_TURBO_TREE_PASS",m["port"]["resulting_tree"])

if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--source",type=Path)
 ap.add_argument("--apply",action="store_true")
 args=ap.parse_args()
 m,p=load()
 print("COMBINED_NATIVE_TURBO_SHA_PASS",m["port"]["patch_sha256"])
 if args.apply:
  assert args.source
  apply_to(args.source,m,p)
