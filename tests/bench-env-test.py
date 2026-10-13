#!/usr/bin/env python3
"""Offline tests for explicit Vulkan environment selection."""
import ast
import unittest
from pathlib import Path

# Extract only the pure function from the standalone harness;
# importing the harness would start real benchmarks.
source = Path(__file__).resolve().parents[1] / "scripts/model-bakeoff.py"
node = next(x for x in ast.parse(source.read_text()).body
            if isinstance(x, ast.FunctionDef) and x.name == "model_env")
namespace = {}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace)
model_env = namespace["model_env"]

class BenchEnvironmentTests(unittest.TestCase):
    def test_no_implicit_nogttspill(self):
        self.assertNotIn("RADV_PERFTEST", model_env({"HOME": "/tmp"}, {"id": "pym"}))

    def test_explicit_optin_only(self):
        env = model_env({"HOME": "/tmp"}, {"radv_perftest": "nogttspill"})
        self.assertEqual(env["RADV_PERFTEST"], "nogttspill")

    def test_explicit_empty_removes_inherited(self):
        env = model_env({"RADV_PERFTEST": "nogttspill"}, {"radv_perftest": ""})
        self.assertNotIn("RADV_PERFTEST", env)

    def test_inherited_profile_is_not_overwritten(self):
        env = model_env({"RADV_PERFTEST": "custom_profile"}, {"id": "pym"})
        self.assertEqual(env["RADV_PERFTEST"], "custom_profile")

    def test_invalid_type_fails(self):
        with self.assertRaises(TypeError):
            model_env({}, {"radv_perftest": 42})

if __name__ == "__main__":
    unittest.main(verbosity=2)
