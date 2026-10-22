#!/usr/bin/env python3
"""Offline reproducibility contract for latest RDNA GPU kernel candidate."""
import json
import re
import unittest
from pathlib import Path

LOCK=Path(__file__).resolve().parents[1]/"tools/benchmarks/rdna_r111_source_lock_20261022.json"

class ReleaseContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(LOCK.read_text())

    def test_expected_frozen_sources(self):
        self.assertEqual(self.d["release_tag"],"v14-097cf33d9-r111")
        self.assertEqual(self.d["upstream_base_full_sha"],"097cf33d9499b1eade67d51e16d7c75427e7b267")
        self.assertEqual(self.d["expected_patched_tree"],"e51b1023a42b1183c3fca8b93be677ffa4cb194b")

    def test_exact_patch_manifest(self):
        d=self.d
        self.assertEqual(d["patch_count"],14)
        self.assertEqual(len(d["patch_sha256"]),14)
        for name,digest in d["patch_sha256"].items():
            self.assertRegex(name,r"^00[0-1][0-9]-rdna-boosts-.*\.patch$")
            self.assertRegex(digest,r"^[0-9a-f]{64}$")

    def test_unknown_gpu_target_not_pretend_certified(self):
        d=self.d
        self.assertEqual(d["gpu_target_under_test"],"gfx1103")
        self.assertFalse(d["upstream_explicitly_validated_gfx1103"])
        self.assertFalse(d["flashnext_gt20_tps_certified"])
        self.assertFalse(d["production_approved"])

    def test_source_and_build_gates(self):
        d=self.d
        self.assertEqual(d["codespace_cpu_binary_compilation"],"passed")
        self.assertEqual(d["codespace_hip_configuration"],"passed")
        self.assertIn(d["codespace_hip_compilation"],("pending","passed"))
        self.assertEqual(d["cloud9_gpu_qualification"],"pending")

if __name__=="__main__":
    unittest.main(verbosity=2)
