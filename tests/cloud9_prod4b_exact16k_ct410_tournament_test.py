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
