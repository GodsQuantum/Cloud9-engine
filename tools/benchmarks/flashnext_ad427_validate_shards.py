#!/usr/bin/env python3
"""Offline fail-closed shard manifest inspection; no model weights loaded.

A manifest is pinned to the exact HF snapshot SHA. Model files are read-only.
Use --sha256 to hash all shards only after the download completes.
"""
import argparse,hashlib,json,re
from pathlib import Path,PurePosixPath

def check(manifest:dict,root:Path,hash_all:bool=False)->dict:
    files=manifest["files"]
    if len(files)!=manifest["expected_shards"] or not files:
        raise ValueError("shard count mismatch")
    if sum(x["size"] for x in files)!=manifest["expected_bytes"]:
        raise ValueError("total bytes mismatch")
    seen=set();bad=[]
    for idx,entry in enumerate(files,1):
        rel=entry["path"]
        pp=PurePosixPath(rel)
        if pp.is_absolute() or any(s in ("..",".") for s in pp.parts) or len(pp.parts)!=2:
            raise ValueError("unsafe shard path")
        if rel in seen:
            raise ValueError("duplicate shard path")
        seen.add(rel)
        if not re.search(rf"-{idx:05d}-of-{len(files):05d}\.gguf$",rel):
            raise ValueError("out-of-order shard")
        digest=entry["sha256"]
        if not re.fullmatch("[0-9a-f]{64}",digest):
            raise ValueError("invalid sha256")
        f=root/rel
        if not f.is_file() or f.is_symlink():
            bad.append((rel,"missing/not_regular"))
            continue
        if f.stat().st_size!=entry["size"]:
            bad.append((rel,"size_mismatch"))
            continue
        if hash_all:
            h=hashlib.sha256()
            with f.open("rb") as reader:
                for block in iter(lambda:reader.read(8*1024*1024),b""):
                    h.update(block)
            if h.hexdigest()!=digest:
                bad.append((rel,"sha256_mismatch"))
    if bad:
        raise ValueError("incomplete/invalid GGUF shards: "+repr(bad[:8]))
    return {"ok":True,"shards":len(files),"bytes":manifest["expected_bytes"],
            "sha256_verified":hash_all,"root":str(root)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,default=Path(__file__).with_name("flashnext_ad427_hf_manifest_20261022.json"))
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--sha256",action="store_true")
    args=p.parse_args()
    print(json.dumps(check(json.loads(args.manifest.read_text()),args.root,args.sha256),indent=2))

if __name__=="__main__":main()
