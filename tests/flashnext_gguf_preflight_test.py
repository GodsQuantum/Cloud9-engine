#!/usr/bin/env python3
"""Offline-only GGUF metadata preflight contract tests."""
from pathlib import Path
import importlib.util
import struct
import tempfile
import unittest

P = Path(__file__).resolve().parents[1] / "tools/benchmarks/flashnext_gguf_preflight_20261022.py"
spec = importlib.util.spec_from_file_location("ggufmeta", P)
meta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(meta)

def s(v):
    b = v.encode()
    return struct.pack("<Q", len(b)) + b

def fixture(path, arch, n=3, split=None, mtp=0):
    vals = [("general.architecture", 8, s(arch)),
            (f"{arch}.context_length", 4, struct.pack("<I", 262144)),
            ("general.name", 8, s("test fixture"))]
    if mtp:
        vals.append((f"{arch}.nextn_predict_layers", 4, struct.pack("<I", mtp)))
    if split is not None:
        ix, count, total = split
        vals += [("split.count", 4, struct.pack("<I", count)),
                 ("split.no", 4, struct.pack("<I", ix)),
                 ("split.tensors.count", 4, struct.pack("<I", total))]
    b = b"GGUF" + struct.pack("<IQQ", 3, n, len(vals))
    b += b"".join(s(name) + struct.pack("<I", t) + v for name, t, v in vals)
    path.write_bytes(b)

class TestGGUFMetadata(unittest.TestCase):
    def test_single_mtp(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)/"qwen35moe.gguf"
            fixture(p, "qwen35moe", mtp=1)
            result = meta.validate_split_group([p])
            self.assertEqual(result["architecture"], "qwen35moe")
            self.assertEqual(result["mtp_metadata"]["qwen35moe.nextn_predict_layers"], 1)
            self.assertEqual(result["context_metadata"]["qwen35moe.context_length"], 262144)
            self.assertEqual(result["status"], "metadata_only_not_gpu_certified")

    def test_two_shards_complete(self):
        with tempfile.TemporaryDirectory() as root:
            a = Path(root)/"Flash-00001-of-00002.gguf"
            b = Path(root)/"Flash-00002-of-00002.gguf"
            fixture(a, "qwen4exp", n=3, split=(0,2,5))
            fixture(b, "qwen4exp", n=2, split=(1,2,5))
            x = meta.validate_split_group([a,b])
            self.assertEqual(x["shards"], 2)
            self.assertEqual(x["architecture"], "qwen4exp")

    def test_missing_shard_refused(self):
        with tempfile.TemporaryDirectory() as root:
            a = Path(root)/"Flash-00001-of-00002.gguf"
            fixture(a, "qwen4exp", split=(0,2,3))
            with self.assertRaises(meta.GGUFError):
                meta.validate_split_group([a])

    def test_duplicate_shard_refused(self):
        with tempfile.TemporaryDirectory() as root:
            a = Path(root)/"Flash-00001-of-00002.gguf"
            fixture(a, "qwen4exp", split=(0,2,3))
            with self.assertRaises(meta.GGUFError):
                meta.validate_split_group([a,a])

    def test_truncated_metadata_refused(self):
        with tempfile.TemporaryDirectory() as root:
            a = Path(root)/"bad.gguf"
            a.write_bytes(b"GGUF\x03\x00\x00\x00")
            with self.assertRaises(meta.GGUFError):
                meta.parse_metadata(a)

    def test_non_gguf_refused(self):
        with tempfile.TemporaryDirectory() as root:
            a=Path(root)/"not.gguf"
            a.write_bytes(b"WRONG" + b"\x00"*20)
            with self.assertRaises(meta.GGUFError):
                meta.parse_metadata(a)

    def test_tensor_count_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as root:
            a=Path(root)/"bad-00001-of-00002.gguf"
            b=Path(root)/"bad-00002-of-00002.gguf"
            fixture(a,"qwen4exp",n=3,split=(0,2,7))
            fixture(b,"qwen4exp",n=2,split=(1,2,7))
            with self.assertRaises(meta.GGUFError):
                meta.validate_split_group([a,b])

    def test_split_header_count_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as root:
            a=Path(root)/"bad-00001-of-00002.gguf"
            b=Path(root)/"bad-00002-of-00002.gguf"
            fixture(a,"qwen4exp",n=3,split=(0,2,5))
            fixture(b,"qwen4exp",n=2,split=(1,3,5))
            with self.assertRaises(meta.GGUFError):
                meta.validate_split_group([a,b])

    def test_mixed_arch_refused(self):
        with tempfile.TemporaryDirectory() as root:
            a=Path(root)/"mix-00001-of-00002.gguf"
            b=Path(root)/"mix-00002-of-00002.gguf"
            fixture(a,"qwen4exp",split=(0,2,6))
            fixture(b,"qwen35moe",split=(1,2,6))
            with self.assertRaises(meta.GGUFError):
                meta.validate_split_group([a,b])

if __name__ == "__main__":
    unittest.main(verbosity=2)
