#!/usr/bin/env python3
"""Guarantee GPU experiment scripts do not secretly force RADV nogttspill."""
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RadvDefaultsTests(unittest.TestCase):
    def test_hardware_gate_no_forced_nogttspill(self):
        source = (ROOT / "scripts/hardware-gate.sh").read_text()
        self.assertNotIn('}nogttspill', source)
        self.assertIn('env_args=()', source)
        self.assertIn('"$dir/bin/llama-server"', source)

    def test_fresh_bench_no_implicit_nogttspill(self):
        source = (ROOT / "scripts/fresh-run-bench.py").read_text()
        tree = ast.parse(source)
        self.assertIn('env=os.environ.copy()', source)
        assignments = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == "env"
                and isinstance(target.slice, ast.Constant)
                and target.slice.value == "RADV_PERFTEST"
                for target in node.targets
            )
        ]
        self.assertEqual(assignments, [])
        self.assertIn('"radv_perftest_effective":os.environ.get("RADV_PERFTEST","")', source)

    def test_bakeoff_manifest_only(self):
        source = (ROOT / "scripts/model-bakeoff.py").read_text()
        self.assertIn('if "radv_perftest" in model:', source)
        self.assertIn('result["radv_perftest_effective"]', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
