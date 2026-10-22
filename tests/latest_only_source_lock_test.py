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
  self.assertEqual(r['rdna']['release_tag'],'v14-097cf33d9-r112')
  self.assertEqual(r['strata']['release_tag'],'v0.2.2')
  self.assertEqual(r['atomic']['release_tag'],'b10298-2.0.0')
 def test_strict_commit_and_patch_manifest(self):
  r=self.d['github_repositories']
  for k in ('rdna','upstream','prism','atomic'):
   v=r[k]; self.assertRegex(v.get('commit',v.get('release_commit','')),r'^[0-9a-f]{40}$')
  self.assertEqual(len(r['rdna']['patch_sha256']),14)
  self.assertRegex(r['rdna']['expected_tree'],r'^[0-9a-f]{40}$')
 def test_ci_only_current_source(self):
  a=(R/'.github/workflows/hip-r112-gfx1103-latest-lab.yml').read_text()
  b=(R/'.github/workflows/latest-upstream-prism-vulkan-lab.yml').read_text()
  self.assertIn('r112',a)
  self.assertNotIn('r111',a)
  self.assertIn('latest_engine_sources_20261023.json',a+b)
  self.assertIn('LATEST_CHANGED_REPIN_REQUIRED',b)
  self.assertFalse((R/'.github/workflows/hip-r111-gfx1103-lab.yml').exists())
 def test_no_false_gpu_certification(self):
  self.assertFalse(self.d['production_approved'])
  self.assertFalse(self.d['flashnext_gt20_tps_certified'])
  for i in self.d['github_repositories'].values():self.assertFalse(i['gpu_benchmark_certified'])
if __name__=='__main__':unittest.main(verbosity=2)
