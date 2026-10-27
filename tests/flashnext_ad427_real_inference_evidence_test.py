import hashlib
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class FlashNextLiveInferencesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record=json.loads((ROOT/'certification/flashnext_ad427_real_inference_20261027.json').read_text())

    def test_genuine_target_and_draft(self):
        r=self.record
        self.assertEqual(r['main_gguf_bytes'],94525394976)
        self.assertEqual(r['draft_gguf_bytes'],3639245152)
        self.assertTrue(r['MTP_d2t_real_math_925_pass'])
        self.assertTrue(r['vulkan_qwen4exp_synthetic_graph_pass'])
        self.assertFalse(r['native_GPU_production_promoted'])

    def test_source_patch_hash_and_scope(self):
        r=self.record
        patch=ROOT/r['native_patch']
        self.assertEqual(hashlib.sha256(patch.read_bytes()).hexdigest(),r['native_patch_sha256'])
        body=patch.read_text()
        self.assertIn('TENSOR_READ_LAZY',body)
        self.assertIn('qwen4exp_demand_paged',body)
        self.assertIn('init_mappings(!qwen4exp_demand_paged',body)
        self.assertTrue(r['production_unchanged'])
        self.assertEqual(r['oom_kills_ct410'],0)

    def test_real_three_task_metrics_and_cold_warm_control(self):
        r=self.record
        done=[x for x in r['attempts'] if x['full_three_task_quality_valid']]
        self.assertGreaterEqual(len(done),4)
        self.assertTrue(all(len(x['tasks'])==3 and x['tasks'][0]['correct_math'] for x in done))
        self.assertGreater(r['best_verified_warm_no_cache_tps'],r['native_auto_moe_cache_3task_tps'])
        self.assertGreater(r['native_auto_moe_cache_3task_tps'],r['baseline_cold_no_cache_tps'])
        self.assertFalse(r['target_above_20_tps_achieved'])
        self.assertFalse(r['historic_record_reproduced'])
        self.assertEqual(r['recommended_live_config_change'],'NONE')

    def test_gpu_expert_layer_offload_rejected_on_measurement(self):
        run=self.record["gpu_more_expert_layer_trial"]
        self.assertEqual(run["native_cpu_moe_layers"],44)
        self.assertEqual(run["additional_gpu_expert_layers"],4)
        self.assertLess(run["math_tps"],2.53)
        self.assertFalse(run["all_three_tasks_quality_valid"])
        self.assertTrue(run["no_oom"])
        self.assertFalse(run["production_promoted"])
        self.assertFalse(self.record["gpu_expert_offload_44_layers_is_winner"])

    def test_gpu_log_transcripts(self):
        path=ROOT/'certification/evidence/2026-10-27'
        log=(path/'oct27_flash_stage_trace_fullGPU_01.txt').read_text()
        self.assertIn('model loaded',log)
        self.assertIn('draft acceptance',log)
        self.assertIn('loading draft model',log)
        self.assertIn('FRSPEC-LAB: mmap initialized',log)

if __name__=='__main__':unittest.main()
