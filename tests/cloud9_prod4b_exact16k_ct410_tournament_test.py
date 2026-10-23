#!/usr/bin/env python3
"""CT410-only lab backend A/B contract. No GPU use in these tests."""
from contextlib import redirect_stdout
from io import StringIO
import importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('cloud9_ct410_ab',ROOT/'tools/benchmarks/cloud9_prod4b_exact16k_ct410_tournament.py')
M=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

class PinnedCt410Tournament(unittest.TestCase):
 def test_all_engines_use_one_guest_and_exact_model(self):
  self.assertEqual(M.CT,['sudo','-n','pct','exec'])
  self.assertEqual(M.ct410_path(M.VULKAN),str(M.VULKAN))
  self.assertEqual(M.ct410_path(M.PROD),str(M.PROD))
  self.assertIn('/srv/lxc/ia-compute/data/models/',str(M.MODEL))
  self.assertIn('16384',M.FLAGS)
  self.assertIn('draft-mtp',M.FLAGS)
  self.assertIn('--no-spec-draft-backend-sampling',M.FLAGS)
  with self.assertRaises(ValueError):M.ct410_path('/etc/passwd')
 def test_exact_pins_with_no_prod_symlink(self):
  self.assertEqual(set(M.CANDIDATES),{'vulkan9ff','hipoff','hipon','hipf32'})
  self.assertNotIn('/current/',str(M.PROD))
  self.assertNotIn('/current/',str(M.VULKAN))
  self.assertNotIn('/current/',str(M.HIP))
  self.assertEqual(len(set(M.EXPECTED_SHA.values())),3)
  self.assertNotEqual(M.PROD,M.VULKAN)
  self.assertNotEqual(M.VULKAN,M.HIP)
 def test_ablation_flags_are_distinct_and_explicit(self):
  self.assertEqual(M.HIP_ENVS['hipoff']['GGML_CUDA_MMB'],'0')
  self.assertEqual(M.HIP_ENVS['hipon']['GGML_CUDA_MMB'],'1')
  self.assertEqual(M.HIP_ENVS['hipf32']['GGML_CUDA_MMF32'],'1')
  self.assertFalse(any('GGML_CUDA_MMB=' in e for e in M.env_for(M.PROD,'hipon')))
  self.assertTrue(any('GGML_CUDA_MMB=1' in e for e in M.env_for(M.HIP,'hipon')))
 def test_actual_llama_cpp_timings_with_prompt_token_counts(self):
  raw=('log: prompt eval time = 55106.80 ms / 16330 tokens '
       '(3.37 ms per token, 296.33 tokens per second)\\n'
       'log: eval time = 2423.05 ms / 74 tokens '
       '(32.74 ms per token, 30.54 tokens per second)')
  t=M.parse_llama_timing(raw)
  self.assertEqual(t['speed_tps'],{'pp':296.33,'tg':30.54})
  self.assertEqual(t['token_counts'],{'pp':16330,'tg':74})
  self.assertTrue(t['full_16k_tokens_measured'])
  self.assertTrue(t['timings_parseable'])

 def test_context_capacity_does_not_imply_full_prefill(self):
  log=('llama_perf_context_print: prompt eval time = 398.08 ms / 55 tokens '
       '(7.24 ms per token, 138.16 tokens per second)\\n'
       'llama_perf_context_print: eval time = 1023.61 ms / 39 tokens '
       '(26.94 ms per token, 37.12 tokens per second)')
  t=M.parse_llama_timing(log)
  self.assertEqual(t['speed_tps']['tg'],37.12)
  self.assertEqual(t['token_counts']['pp'],55)
  self.assertFalse(t['full_16k_tokens_measured'])
  self.assertTrue(t['generation_sample_at_least_16_tokens'])

 def test_compact_cli_timings_do_not_falsely_claim_token_depth(self):
  t=M.parse_llama_timing('Prompt: 322.22 t/s\\nGeneration: 31.32 t/s')
  self.assertTrue(t['timings_parseable'])
  self.assertEqual(t['token_counts'],{})
  self.assertFalse(t['full_16k_tokens_measured'])
  self.assertFalse(t['generation_sample_at_least_16_tokens'])

 def test_incomplete_or_fake_timings_cannot_pass(self):
  self.assertFalse(M.parse_llama_timing('nothing useful')['timings_parseable'])
  self.assertFalse(M.parse_llama_timing('Prompt: 50.0 t/s')['timings_parseable'])
  self.assertFalse(M.parse_llama_timing('Prompt: 0.0 t/s\\nGeneration: 50.0 t/s')['timings_parseable'])

 def test_near_full_needle5_is_reproducible_from_historical_proof(self):
  import hashlib
  fixture=M.near_full_context_fixture()
  self.assertEqual(M.NEEDLE5_REPEATS,33)
  self.assertEqual(hashlib.sha256(fixture.encode()).hexdigest(),
                   '487958eadd17a6b7f2ebab676373b7e9aadad98849361e688aecb636b24a592f')
  self.assertLess(len(fixture),120000)
  self.assertTrue(all(v in fixture for v in M.NEEDLE5_CODES.values()))
  self.assertIn('--no-context-shift',M.FLAGS)

 def test_strict_five_needle_json_quality_grading(self):
  exact='{"alpha":"VTR-9385","beta":"MQR-5281","gamma":"BDV-1947","delta":"JKP-6032","omega":"FNC-7824"}'
  correct=M.grade_needle5_output('model says: '+exact+'\\nperf timing')
  self.assertTrue(correct['passed'])
  self.assertEqual(correct['matching_codes'],5)
  corrupt=exact.replace('FNC-7824','FNC-0000')
  wrong=M.grade_needle5_output('model says: '+corrupt)
  self.assertFalse(wrong['passed'])
  self.assertEqual(wrong['matching_codes'],4)
  absent=M.grade_needle5_output('unstructured answer')
  self.assertFalse(absent['evaluated'])
  self.assertFalse(absent['passed'])

 def test_near_full_without_gpu_stays_preflight_only(self):
  with patch.object(M,'admission',return_value={'allow':False,'reasons':['IO_PSI_GE_5']}):
   with patch.object(M,'near_full_context_fixture',side_effect=AssertionError('DO_NOT_GENERATE_AFTER_DENIAL')):
    with patch.object(sys,'argv',['bench','--profile','near-full','--challenger','hipf32']),redirect_stdout(StringIO()) as out:
     M.main()
  result=json.loads(out.getvalue())
  self.assertEqual(result['status'],'PREFLIGHT_ONLY')
  self.assertEqual(result['profile'],'near-full')

 def test_preflight_never_launches_model(self):
  guard={'allow':False,'reasons':['IO_PSI_GE_5']}
  for c in M.CANDIDATES:
   with self.subTest(challenger=c):
    with patch.object(M,'admission',return_value=guard),patch.object(M,'run_trial',side_effect=AssertionError('GPU_RUN_NOT_PERMITTED')):
     with patch.object(sys,'argv',['bench','--challenger',c]),redirect_stdout(StringIO()) as out:
      M.main()
     result=json.loads(out.getvalue())
    self.assertEqual(result['status'],'PREFLIGHT_ONLY')
    self.assertEqual(result['challenger'],c)
 def test_execute_denied_exit3_even_if_hip_requested(self):
  guard={'allow':False,'reasons':['RAM_BELOW_32_GIB','IO_PSI_GE_5']}
  with patch.object(M,'admission',return_value=guard),patch.object(M,'run_trial',side_effect=AssertionError('NO_GPU')):
   with patch.object(sys,'argv',['bench','--execute','--challenger','hipon']),redirect_stdout(StringIO()) as out:
    with self.assertRaises(SystemExit) as stop: M.main()
  self.assertEqual(stop.exception.code,3)
  self.assertEqual(json.loads(out.getvalue())['status'],'GPU_BLOCKED')
if __name__=='__main__':unittest.main(verbosity=2)
