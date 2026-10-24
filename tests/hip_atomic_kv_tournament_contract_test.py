#!/usr/bin/env python3
"""Offline contract for phase-optimization comparison candidates.

No GPU, network, model files or production execution is performed here.
"""
from pathlib import Path
import importlib.util
import unittest

BENCH = Path(__file__).resolve().parents[1] / "tools/benchmarks/live_quality12_mtp_20261022.py"


def load():
    spec = importlib.util.spec_from_file_location("live_quality_contract", BENCH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HybridCandidateSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load()

    def test_same_weights_between_all_four_engines(self):
        names = ("atomic4b", "atomic4b-q8v", "atomic4b-hip-turbo3", "atomic4b-hip-q8v", "b11798-4b", "rdna-r111-vulkan-4b", "rdna-r111-hip-4b", "s1-head-4b")
        specs = [self.module.CANDIDATES[name] for name in names]
        self.assertEqual(len({str(s["model"]) for s in specs}), 1)
        self.assertEqual({s["expected_bytes"] for s in specs}, {2790000800})
        self.assertEqual({s["flags"][0:2][1] for s in specs}, {"8192"})

    def test_atomic_ab_changes_only_v_cache(self):
        atomic = self.module.CANDIDATES["atomic4b"]
        control = self.module.CANDIDATES["atomic4b-q8v"]
        self.assertEqual(atomic["bin"], control["bin"])
        self.assertEqual(atomic["model"], control["model"])
        self.assertEqual(atomic["flags"][:-1], control["flags"][:-1])
        self.assertEqual(atomic["flags"][-1], "turbo3")
        self.assertEqual(control["flags"][-1], "q8_0")

    def test_hip_and_vulkan_same_explicit_flags(self):
        a = self.module.CANDIDATES["rdna-r111-vulkan-4b"]
        b = self.module.CANDIDATES["rdna-r111-hip-4b"]
        self.assertEqual(a["flags"], b["flags"])
        self.assertIn("actions-20261023", str(b["bin"]))
        self.assertNotIn("current/", str(b["bin"]))

    def test_atomic_hip_has_identical_backend_flags_and_lab_paths(self):
        c = self.module.CANDIDATES
        self.assertEqual(c["atomic4b-hip-turbo3"]["flags"], c["atomic4b"]["flags"])
        self.assertEqual(c["atomic4b-hip-q8v"]["flags"], c["atomic4b-q8v"]["flags"])
        self.assertEqual(c["atomic4b-hip-turbo3"]["bin"], c["atomic4b-hip-q8v"]["bin"])
        self.assertNotEqual(c["atomic4b-hip-turbo3"]["bin"], c["atomic4b"]["bin"])
        self.assertIn("rocm-20261023", str(c["atomic4b-hip-turbo3"]["bin"]))
        self.assertNotIn("/current/", str(c["atomic4b-hip-turbo3"]["bin"]))

    def test_guard_remains_fail_closed(self):
        code = BENCH.read_text()
        self.assertIn('os.environ.get("CLOUD9_GPU_COEXIST_ADMITTED")=="1"', code)
        self.assertIn('"--spec-type","draft-mtp","--spec-draft-n-max","2"', code)
        self.assertIn('"production_eligible":False', code)
        self.assertIn('assert not result_path.exists() and not log_path.exists()', code)


if __name__ == "__main__":
    unittest.main()
