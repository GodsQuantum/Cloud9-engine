#!/usr/bin/env python3
"""Fail-closed offline manifest and shard integrity tests."""
import hashlib,importlib.util,copy,unittest
from pathlib import Path
from tempfile import TemporaryDirectory

module=Path(__file__).resolve().parents[1]/"tools/benchmarks/flashnext_ad427_validate_shards.py"
spec=importlib.util.spec_from_file_location("gguf_sha",module)
h=importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
sub="FlashNext-AD427"
def fixture(root):
    a=[]
    for i in range(1,4):
        content=bytes([i])*i*1000
        rel=f"{sub}/{sub}-{i:05d}-of-00003.gguf"
        dest=root/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(content)
        a.append({"path":rel,"size":len(content),"sha256":hashlib.sha256(content).hexdigest()})
    return {"files":a,"expected_shards":3,"expected_bytes":sum(x["size"] for x in a)}

class ManifestIntegrity(unittest.TestCase):
    def test_pinned_snapshot_real(self):
        import json
        p=module.with_name("flashnext_ad427_hf_manifest_20261022.json")
        m=json.loads(p.read_text())
        self.assertEqual(m["revision"],"c4f844865189c05eeaa05406576a8d7d4931df5c")
        self.assertEqual(m["expected_shards"],33)
        self.assertEqual(m["expected_bytes"],94525394976)
        self.assertEqual(len(m["files"]),33)
        self.assertEqual(sum(x["size"] for x in m["files"]),94525394976)
    def test_positive_full_hash(self):
        with TemporaryDirectory() as td:
            root=Path(td)
            m=fixture(root)
            self.assertTrue(h.check(m,root,True)["sha256_verified"])
    def test_missing_file_refused(self):
        with TemporaryDirectory() as td:
            root=Path(td);m=fixture(root)
            (root/m["files"][0]["path"]).unlink()
            with self.assertRaises(ValueError):h.check(m,root)
    def test_corrupt_file_refused(self):
        with TemporaryDirectory() as td:
            root=Path(td);m=fixture(root)
            p=root/m["files"][0]["path"];p.write_bytes(b"x"*p.stat().st_size)
            with self.assertRaises(ValueError):h.check(m,root,True)
    def test_wrong_size_refused(self):
        with TemporaryDirectory() as td:
            root=Path(td);m=fixture(root)
            p=root/m["files"][0]["path"];p.write_bytes(b"oops")
            with self.assertRaises(ValueError):h.check(m,root,True)
    def test_traversal_refused(self):
        with TemporaryDirectory() as td:
            root=Path(td);m=fixture(root)
            m["files"][0]["path"]="../escape-00001-of-00003.gguf"
            with self.assertRaises(ValueError):h.check(m,root)
    def test_total_bytes_refused(self):
        with TemporaryDirectory() as td:
            root=Path(td);m=fixture(root)
            m["expected_bytes"]+=1
            with self.assertRaises(ValueError):h.check(m,root)
    def test_wrong_index_refused(self):
        with TemporaryDirectory() as td:
            root=Path(td);m=fixture(root)
            m["files"].reverse()
            with self.assertRaises(ValueError):h.check(m,root)
    def test_bad_sha_refused(self):
        with TemporaryDirectory() as td:
            root=Path(td);m=fixture(root)
            m["files"][0]["sha256"]="not a SHA"
            with self.assertRaises(ValueError):h.check(m,root,True)

if __name__=="__main__":unittest.main(verbosity=2)
