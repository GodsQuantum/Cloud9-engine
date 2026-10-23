#!/usr/bin/env python3
"""S1 v64 current donor and Cloud9 GPU unqualified until verified."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class CurrentS1Source(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.s=json.loads((ROOT/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())
  cls.w=(ROOT/'.github/workflows/lab-latest-s1-v64-vulkan.yml').read_text()
 def test_exact_source_and_lab_gate(self):
  d=self.s['github_repositories']['s1']
  self.assertEqual(d['branch'],'s1-public')
  self.assertEqual(d['commit'],'28316b0e6658ae57575d557dcf41ba09836ceb71')
  self.assertFalse(d['gpu_benchmark_certified'])
  self.assertEqual(self.s['lab_candidate_binary_sha256']['s1-head-4b'], '5af45b72c01f8ebb2adb4db11427ac97406f60d7779a0926a846952c8abc0db6')
 def test_crossbuilt_not_gpu_promoted(self):
  self.assertIn('GGML_VULKAN=ON',self.w)
  self.assertIn('verify_latest_sources.py --candidate s1-head-4b',self.w)
  self.assertIn('LATEST_S1_MOVED_REPIN_REQUIRED',self.w)
  self.assertIn('NOT_GPU_QUALIFIED.txt',self.w)
  self.assertNotIn('pct exec',self.w)
 def test_current_tournament_gates_candidate(self):
  import importlib.util
  p=ROOT/'tools/benchmarks/live_quality12_mtp_20261022.py'
  spec=importlib.util.spec_from_file_location('current_tournament',p)
  m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  self.assertIn('s1-head-4b',m.LATEST_ONLY_CANDIDATES)
  self.assertIn('latest-s1-vulkan-20261023',str(m.CANDIDATES['s1-head-4b']['bin']))
  self.assertEqual(m.CANDIDATES['s1-head-4b']['expected_bytes'],2790000800)
if __name__=='__main__':unittest.main(verbosity=2)
