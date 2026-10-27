#!/usr/bin/env python3
"""Offline contract: current tournament has pinned latest source; legacy output is historical only."""
import json,re,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class LatestOnly(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=json.loads((R/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())
 def test_latest_release_tags(self):
  r=self.d['github_repositories']
  self.assertEqual(r['rdna']['release_tag'],'v15-6050b467c-r142')
  self.assertEqual(r['strata']['release_tag'],'v0.2.6')
  self.assertEqual(r['atomic']['release_tag'],'b10298-2.0.0')
 def test_strict_commit_and_patch_manifest(self):
  r=self.d['github_repositories']
  for k in ('rdna','upstream','prism','atomic','s1'):
   v=r[k]; self.assertRegex(v.get('commit',v.get('release_commit','')),r'^[0-9a-f]{40}$')
  self.assertEqual(len(r['rdna']['archived_r120_provenance']['patch_sha256']),14)
  self.assertRegex(r['rdna']['archived_r120_provenance']['expected_tree'],r'^[0-9a-f]{40}$')
 def test_ci_only_current_source(self):
  a=(R/'.github/workflows/hip-r120-gfx1103-latest-lab.yml').read_text()
  b=(R/'.github/workflows/latest-upstream-prism-vulkan-lab.yml').read_text()
  self.assertIn('r120',a) # archived LAB is not a latest candidate
  self.assertNotIn('r111',a)
  self.assertIn('latest_engine_sources_20261023.json',a+b)
  self.assertIn('Reject source changes during compilation',b)
  self.assertIn('LATEST_CHANGED_REPIN_REQUIRED',b)
  self.assertFalse((R/'.github/workflows/hip-r111-gfx1103-lab.yml').exists())
 def test_live_runner_refuses_legacy_engine_versions(self):
  import importlib.util
  src=R/'tools/benchmarks/live_quality12_mtp_20261022.py'
  mod=importlib.util.module_from_spec(importlib.util.spec_from_file_location('quality_latest_only',src))
  import importlib.util as U
  U.module_from_spec # noqa
  spec=U.spec_from_file_location('quality_latest_only',src)
  spec.loader.exec_module(mod)
  self.assertFalse({'b11798-4b','b11798-hermes9b','rdna-r111-vulkan-4b','rdna-r111-hip-4b'} & mod.LATEST_ONLY_CANDIDATES)
  def api(path):
    if 'stew675' in path:key='rdna'
    elif 'AtomicBot-ai' in path:key='atomic'
    elif 'ggml-org' in path:key='upstream'
    elif 'PrismML-Eng' in path:key='prism'
    elif 'vahpetr' in path:key='s1'
    else:raise AssertionError('UNKNOWN_ENDPOINT '+path)
    v=self.d['github_repositories'][key]
    if path.endswith('/releases/latest'):return {'tag_name':v['release_tag']}
    return {'object':{'type':'commit','sha':v.get('release_commit',v.get('commit'))}}
  for name in ('atomic4b','s1-head-4b'):
   self.assertIn(name,mod.LATEST_ONLY_CANDIDATES)
   self.assertEqual(mod.validate_latest_only(name,live_api=api,_test_skip_binary_sha=True)['source_date'],self.d['source_date'])
  for retired in ('rdna-r111-hip-4b','rdna-r120-hip-4b','upstream-master-4b','prism-head-4b','chimera-062-mmb-on'):
   with self.assertRaisesRegex(AssertionError,'RETIRED_ENGINE_GPU_TEST_DENIED'):
    mod.validate_latest_only(retired)
 def test_no_false_gpu_certification(self):
  self.assertFalse(self.d['production_approved'])
  self.assertFalse(self.d['flashnext_gt20_tps_certified'])
  for i in self.d['github_repositories'].values():self.assertFalse(i['gpu_benchmark_certified'])
if __name__=='__main__':unittest.main(verbosity=2)
