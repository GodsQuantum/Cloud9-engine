import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

P = pathlib.Path(__file__).resolve().parents[1] / "tools/local_agents/c10_multiagent_capacity.py"
spec = importlib.util.spec_from_file_location("c10_capacity", P)
# The benchmark references existing local agents module, inject package directory only in test import.
import sys
sys.path.insert(0, str(P.parent))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class CapacityGuardTest(unittest.TestCase):
    def test_only_opt_in_exact_model(self):
        with self.assertRaisesRegex(ValueError, "ONLY_EXACT_CHIMERA_LAB_ALLOWED"):
            b.preflight("production-model", "http://x", "http://y", "localhost")

    def test_guardian_denies_without_worker_start(self):
        with mock.patch.object(b, "fetch_json", side_effect=[{"worker_model": b.MODEL_ID}]), \
             mock.patch.object(b, "guardian_check", return_value={"allow": False, "reasons": ["PSI"]}):
            with self.assertRaisesRegex(ValueError, "OFFICIAL_GUARDIAN_DENIED"):
                b.preflight(b.MODEL_ID, "http://x", "http://y", "localhost")

    def test_unloaded_worker_denied_before_gpu_guard(self):
        with mock.patch.object(b, "fetch_json", return_value={"worker_model": None}), \
             mock.patch.object(b, "guardian_check") as guard:
            with self.assertRaisesRegex(ValueError, "EXACT_WORKER_NOT_ALREADY_LOADED"):
                b.preflight(b.MODEL_ID, "http://x", "http://y", "localhost")
            guard.assert_not_called()

    def test_worker_native_slots_grounded_not_client_count(self):
        with mock.patch.object(b, "fetch_json", side_effect=[{"worker_model": b.MODEL_ID}, [{"id": 0}]]), \
             mock.patch.object(b, "guardian_check", return_value={"allow": True, "mem_available_gib": 28}):
            d = b.preflight(b.MODEL_ID, "http://x", "http://y", "localhost")
            self.assertEqual(d["native_slots"], 1)
        self.assertFalse(b.summarize([{"phase":"tool","passed":True,"wall_seconds":1}], 1)["server_true_parallelism_proven"])

    def test_busy_worker_is_rejected(self):
        with mock.patch.object(b,"fetch_json",side_effect=[{"worker_model":b.MODEL_ID},[{"id":0,"is_processing":True}]]), mock.patch.object(b,"guardian_check",return_value={"allow":True}):
            with self.assertRaisesRegex(ValueError,"NATIVE_WORKER_BUSY"):
                b.preflight(b.MODEL_ID,"http://x","http://y","localhost")

    def test_missing_or_empty_slots_block(self):
        for invalid in ([], {}, None, [1]):
            with self.assertRaises(ValueError):
                b.validate_slots(invalid)

    def test_percentile_nearest_rank_no_invention(self):
        self.assertIsNone(b.p95([]))
        self.assertEqual(b.p95([3, 1, 2]), 3)
        self.assertEqual(b.p95([1, 2, 5, 3, 4]), 5)

    def test_dry_run_makes_no_network_calls_or_files(self):
        with mock.patch.object(b, "fetch_json") as net, \
             mock.patch.object(b, "guardian_check") as guard, \
             redirect_stdout(io.StringIO()) as stdout:
            b.main([])
        self.assertEqual(json.loads(stdout.getvalue())["status"], "dry_run_only")
        net.assert_not_called()
        guard.assert_not_called()

    def test_execute_requires_fresh_output(self):
        with tempfile.TemporaryDirectory() as t:
            out = pathlib.Path(t) / "already.json"
            out.write_text("{}")
            with self.assertRaises(SystemExit):
                b.main(["--execute", "--output", str(out)])
            self.assertEqual(out.read_text(), "{}")

    def test_strict_simulated_tools_in_source(self):
        src = P.read_text()
        self.assertIn('tool_choice": "required"', src)
        self.assertIn('parallel_tool_calls": False', src)
        self.assertIn('guardian_check', src)
        self.assertIn('worker_model', src)
        self.assertNotIn('systemctl restart', src)
        self.assertNotIn('subprocess.Popen', src)
        self.assertNotIn('pct stop', src)


if __name__ == "__main__":
    unittest.main()
