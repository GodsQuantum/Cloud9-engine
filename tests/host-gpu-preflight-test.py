#!/usr/bin/env python3
"""Offline host preflight tests: never read actual GPU, never modify system."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

GATE = Path(__file__).resolve().parents[1] / "scripts/host-gpu-preflight.py"
GOOD = {
    "gtt_bytes": 2 * 1024**3,
    "mem_available_kb": 36 * 1024**2,
    "io_full_avg10": 0.25,
    "memory_full_avg10": 0.1,
    "swap_pages_delta_200ms": 0,
    "gpu_tasks_d": [],
    "recent_gpu_errors": [],
}

class HostGPUPreflightTests(unittest.TestCase):
    def gate(self, snap, rc, needle=None):
        p = subprocess.run([sys.executable, str(GATE), "--fixture-stdin"],
                           input=json.dumps(snap), text=True,
                           capture_output=True, timeout=4)
        self.assertEqual(p.returncode, rc, p.stdout + p.stderr)
        obj = json.loads(p.stdout)
        self.assertEqual(obj["status"], "PASS" if rc == 0 else "REFUSE")
        if needle:
            self.assertIn(needle, " ".join(obj["problems"]))

    def test_clean_host(self):
        self.gate(GOOD, 0)

    def test_missing_evidence(self):
        bad = copy.deepcopy(GOOD)
        del bad["gtt_bytes"]
        self.gate(bad, 4, "incomplete")

    def test_wedged_other_ct(self):
        bad = copy.deepcopy(GOOD)
        bad["gpu_tasks_d"].append({"pid": 2625774, "wchan": "drm_suballoc_new"})
        self.gate(bad, 4, "blocked GPU")

    def test_gtt_over_budget(self):
        bad = copy.deepcopy(GOOD)
        bad["gtt_bytes"] = 14 * 1024**3
        self.gate(bad, 4, "GTT")

    def test_kernel_error(self):
        bad = copy.deepcopy(GOOD)
        bad["recent_gpu_errors"] = ["amdgpu_vm_validate failed"]
        self.gate(bad, 4, "GPU errors")

    def test_memory_and_io_pressure(self):
        bad = copy.deepcopy(GOOD)
        bad.update(mem_available_kb=8 * 1024**2,
                   io_full_avg10=9, swap_pages_delta_200ms=150)
        self.gate(bad, 4, "available RAM")

    def test_malformed_evidence(self):
        bad = copy.deepcopy(GOOD)
        bad["gpu_tasks_d"] = "unknown"
        self.gate(bad, 4, "invalid evidence")

if __name__ == "__main__":
    unittest.main(verbosity=2)
