#!/usr/bin/env python3
"""Run production router's model_env function in isolation (no GPU or daemon)."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "bin/cloud9-model-router.py"


def router_env_function():
    tree = ast.parse(ROUTER.read_text())
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == "model_env"]
    if len(functions) != 1:
        raise RuntimeError("Router must define exactly one model_env")
    compiled = compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])),
                       str(ROUTER), "exec")
    namespace = {}
    exec(compiled, namespace)
    return namespace["model_env"]


class RouterRadvEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.model_env = router_env_function()

    def test_default_no_radv(self):
        env = self.model_env({"PATH": "/usr/bin"}, {"id": "Pym"})
        self.assertNotIn("RADV_PERFTEST", env)

    def test_inherited_is_preserved_and_source_is_not_modified(self):
        src = {"RADV_PERFTEST": "custom_optimization", "PATH": "/usr/bin"}
        env = self.model_env(src, {"id": "Pym"})
        self.assertEqual(env["RADV_PERFTEST"], "custom_optimization")
        self.assertEqual(src["RADV_PERFTEST"], "custom_optimization")

    def test_explicit_model_value_replaces_not_appends(self):
        env = self.model_env({"RADV_PERFTEST": "existing"},
                             {"radv_perftest": "explicit_custom_flag"})
        self.assertEqual(env["RADV_PERFTEST"], "explicit_custom_flag")

    def test_explicit_model_empty_clears_inherited(self):
        env = self.model_env({"RADV_PERFTEST": "nogttspill"},
                             {"radv_perftest": ""})
        self.assertNotIn("RADV_PERFTEST", env)

    def test_wrong_types_fail_closed(self):
        for value in (None, False, True, 7, [], {}):
            with self.subTest(value=value), self.assertRaises(TypeError):
                self.model_env({}, {"radv_perftest": value})

    def test_live_router_uses_tested_helper_not_implicit_append(self):
        source = ROUTER.read_text()
        tree = ast.parse(source)
        worker = [node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name == "ensure_worker_locked"]
        self.assertEqual(len(worker), 1)
        all_calls = [node for node in ast.walk(worker[0]) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name) and node.func.id == "model_env"]
        self.assertEqual(len(all_calls), 1, "The production router must call the tested function")
        self.assertNotIn('perf.append("nogttspill")', source)
        self.assertIn("radv={env.get(", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
