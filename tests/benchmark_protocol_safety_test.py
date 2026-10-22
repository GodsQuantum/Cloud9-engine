#!/usr/bin/env python3
"""Offline tests: benchmark scripts cannot produce false evidence from fixture bugs."""
import hashlib
import importlib.util
import pathlib
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
TOOL = REPO / "tools/benchmarks"

def load(name):
    p = TOOL / name
    spec = importlib.util.spec_from_file_location(name[:-3], p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

class SyntheticWitnessTest(unittest.TestCase):
    def test_five_unique_markers_ordered(self):
        a = load("synthetic_context_witness_20261022.py")
        text = a.mktext(12)
        seen = [text.index(code) for code in a.CODES.values()]
        self.assertEqual(len(seen), 5)
        self.assertEqual(seen, sorted(seen))
        for code in a.CODES.values():
            self.assertEqual(text.count(code), 1)

    def test_fixture_is_byte_deterministic(self):
        a = load("synthetic_context_witness_20261022.py")
        x = a.mktext(8).encode()
        y = a.mktext(8).encode()
        self.assertEqual(hashlib.sha256(x).digest(), hashlib.sha256(y).digest())

    def test_turboquant_has_native_mtp_and_distinct_port(self):
        p = (TOOL/"atomic_turboquant_context_20261022.py").read_text()
        self.assertIn('"draft-mtp"', p)
        self.assertIn('"turbo3"', p)
        self.assertIn("PORT=18227", p)
        self.assertIn("CLOUD9_GPU_COEXIST_ADMITTED", p)

    def test_live_36_quality_calls_require_lock_and_mtp(self):
        p=(TOOL/"live_quality12_mtp_20261022.py").read_text()
        self.assertIn("CLOUD9_GPU_COEXIST_ADMITTED",p)
        self.assertIn('"--spec-type","draft-mtp"',p)
        self.assertIn('grade.aggregate',p)
        self.assertIn('Path(__file__).resolve().with_name("one_engine_quality_protocol_20261022.py")',p)
        self.assertNotIn('/tmp/cloud9-real-quality-protocol-',p)
        self.assertIn('"b11798-9b"',p)
        self.assertIn('"b11798-4b"',p)
        self.assertIn('"b11798-35b"',p)
        self.assertIn('--thermal-pace',p)
        self.assertIn('--trial-tag',p)
        self.assertIn('re.fullmatch',p)
        self.assertIn('time.monotonic()+120',p)
        self.assertIn('while tctl()>72.0',p)
        self.assertIn('"TEMPERATURE_COOLDOWN_TIMEOUT"',p)
        self.assertIn('start_new_session=True',p)
        self.assertNotIn("systemctl stop",p)
        self.assertNotIn("docker stop",p)

    def test_strata_flashnext_uses_hardware_admission_and_scoped_process(self):
        p = (TOOL/"strata_flashnext_guarded_probe_20261022.py").read_text()
        self.assertIn('OFFICIAL_CT410_ALLOW', p)
        self.assertIn('/run/cloud9-gpu.lock', p)
        self.assertIn('PRODUCTION_GPU_CLIENT', p)
        self.assertIn('GPU_LEASE_LOST', p)
        self.assertIn('HARD_SAFETY', p)
        self.assertIn('--ple-gguf', p)
        self.assertIn('--mmap-experts', p)
        self.assertIn('--mtp', p)
        self.assertIn('os.killpg(proc.pid,signal.SIGTERM)', p)
        self.assertNotIn('systemctl stop', p)
        self.assertNotIn('pct stop', p)

    def test_magnitude_requires_lease_and_no_real_tools(self):
        m = load("magnitude_agentic_protocol_20261022.py")
        p = (TOOL/"magnitude_agentic_protocol_20261022.py").read_text()
        self.assertIn("CLOUD9_GPU_COEXIST_ADMITTED", p)
        self.assertIn('"--method","mtp"', p)
        self.assertIn('"--device","vulkan"', p)
        self.assertIn('"--tuning-budget","2"', p)
        self.assertNotIn("systemctl start", p)
        self.assertNotIn("gh auth", p)
        self.assertEqual(m.PORT,18230)

if __name__ == "__main__":
    unittest.main(verbosity=2)
