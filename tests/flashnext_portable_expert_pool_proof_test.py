import hashlib
import json
import unittest
from pathlib import Path

R=Path(__file__).resolve().parents[1]

class PortableFRSpecExpertPoolLabTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof=json.loads((R/'certification/flashnext_portable_expert_pool_20261027.json').read_text())

    def test_portable_pool_patch_integrity(self):
        e=self.proof
        blob=(R/e['source_patch']).read_bytes()
        self.assertEqual(hashlib.sha256(blob).hexdigest(),e['source_patch_sha256'])
        txt=blob.decode()
        self.assertIn('init_expert_pools',txt)
        self.assertIn('ggml_backend_sched_register_expert_pool',txt)
        self.assertIn('expert_cache_slots',txt)
        self.assertEqual(e['native_base_commit'],'0780e182')
        self.assertEqual(e['isolated_native_commit'],'d51a783d')

    def test_vulkan_expert_pool_and_qwen4exp_qa(self):
        e=self.proof
        self.assertIn('expert pool test PASSED',(R/e['expert_pool_native_log']).read_text())
        x=(R/e['qwen4exp_test_log']).read_text()
        self.assertIn('AMD Radeon 780M',x)
        self.assertIn('8.43e-08',x)
        self.assertEqual(e['expert_pool_backend_test'],'PASS')
        self.assertEqual(e['qwen4exp_synthetic_moe_gpu_test'],'PASS')

    def test_no_false_live_benchmark_or_production_claim(self):
        e=self.proof
        self.assertIsNone(e['hybrid_full_target_and_draft_measured_tps'])
        self.assertFalse(e['goal_above_20tps_met'])
        self.assertFalse(e['production_mutated'])
        self.assertTrue(e['frspec_Q8_reduced_vocab_support_retained_from_base'])
        self.assertEqual(e['runtime_test_admission'],'BLOCKED_EMBEDDINGS_ACTIVE_OR_UNKNOWN')

    def test_lab_runner_selects_pool_explicitly(self):
        src=(R/'tools/qualification/flashnext_ad427_native_smoke.py').read_text()
        self.assertIn("'portable-pool'",src)
        self.assertIn('POOL_BIN',src)
        self.assertIn('--moe-expert-cache',src)
        self.assertIn('--expert-slots',src)
        self.assertIn('readonly_preflight',src)
        self.assertIn('gate.stop_own(child)',src)
        self.assertNotIn('swapoff',src)

if __name__=='__main__':unittest.main()
