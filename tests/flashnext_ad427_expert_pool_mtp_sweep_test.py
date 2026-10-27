import json
import unittest
from pathlib import Path

R=Path(__file__).resolve().parents[1]

class GPUExpertPoolAndMTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof=json.loads((R/'certification/flashnext_ad427_expert_pool_mtp_sweep_20261027.json').read_text())
        cls.by={a['id']:a for a in cls.proof['trials']}

    def test_real_gpu_hybrid_pool_enabled_for_main_not_draft(self):
        x=self.proof['native_pool_backend_diagnostic']
        self.assertIn('144 of 144',x)
        self.assertIn('draft',x)
        self.assertTrue(self.proof['most_recent_synthetic_pool_qa_passed'])
        self.assertTrue(self.proof['native_pool_diagnostic_lab_source_reverted'])
        self.assertTrue(self.proof['host_no_oom_ct410'])
        self.assertTrue(self.proof['no_prod_deployment'])

    def test_matched_3_task_pool_results(self):
        by=self.by
        p0=by['oct27_hybrid_pool0_control_req9_retry']
        p16=by['oct27_pool16_diag_mem_2']
        self.assertTrue(p0['qualified_3_task'])
        self.assertTrue(p16['qualified_3_task'])
        self.assertEqual(p0['gpu_expert_pool_slots'],0)
        self.assertEqual(p16['gpu_expert_pool_slots'],16)
        self.assertGreater(p16['mean_tps'],p0['mean_tps'])
        self.assertLess(p16['mean_tps'],2.685)
        self.assertFalse(by['oct27_hybrid_pool32_req11p5_trial2']['qualified_3_task'])

    def test_mtp_depth_ab_and_quality(self):
        a=self.by['oct27_atomic2_fr_draft2_req9p5']
        b=self.by['oct27_atomic2_fr_draft5_req9p5']
        for t,depth in [(a,2),(b,5)]:
            self.assertEqual(t['draft_depth'],depth)
            self.assertTrue(t['qualified_3_task'])
            self.assertLess(t['mean_tps'],2.685)
            self.assertEqual(len(t['scores']),3)
            self.assertTrue(t['scores'][0]['correct_math'])

    def test_guarded_variants_not_misrepresented_as_benchmarks(self):
        for x in self.proof['trials']:
            if x['status']!='complete':
                self.assertIsNone(x['mean_tps'])
            if x['guardian_rejections']:
                self.assertFalse(x['qualified_3_task'])
        self.assertFalse(self.proof['no_prod_deployment'] is False)
        self.assertGreater(self.proof['original_hof_20260915_tps'],self.proof['historical_best_under_prior_baseline'] and 2.685)

if __name__=='__main__':unittest.main()
