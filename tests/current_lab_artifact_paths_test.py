#!/usr/bin/env python3
"""Offline safety contract for exact current Cloud9 lab candidate paths/hashes."""
import importlib.util
import json
import re
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
S=R/'tools/benchmarks/live_quality12_mtp_20261022.py'
spec=importlib.util.spec_from_file_location('lab_runner_contract',S)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class CurrentArtifactPathContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.lock=json.loads((R/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())
 def test_manifest_retired_archived_upstream_sha(self):
  self.assertNotEqual(self.lock['github_repositories']['upstream']['commit'],'06230cb8775899cceef146c19cd447a947ecac5b')
 def test_archived_runner_paths_still_inspectable(self):
  self.assertIn('latest-upstream-master062-vulkan-20261023/package/bin',str(mod.CANDIDATES['upstream-master-4b']['bin']))
  self.assertIn('latest-rdna-r120-hip-20261023/rdna-hip-artifact/bin',str(mod.CANDIDATES['rdna-r120-hip-4b']['bin']))
  for name in ('chimera-062-mmb-off','chimera-062-mmb-on','chimera-062-mmb-mmf32'):
   self.assertIn('latest-chimera-mmb-r120-on-master062-hip-20261023/chimera-uncertified/bin',str(mod.CANDIDATES[name]['bin']))
 def test_archived_binary_sha_only_not_gpu_certification(self):
  h=self.lock['lab_candidate_binary_sha256']
  names=('upstream-master-4b','rdna-r120-hip-4b','chimera-062-mmb-off','chimera-062-mmb-on','chimera-062-mmb-mmf32')
  for name in names:self.assertRegex(h[name],r'^[0-9a-f]{64}$')
  self.assertEqual({h[n] for n in names if n.startswith('chimera-')},{h['chimera-062-mmb-on']})
  self.assertFalse(self.lock['production_approved'])
  self.assertFalse(self.lock['github_repositories']['upstream']['gpu_benchmark_certified'])
 def test_no_old_fork_as_fresh_candidate(self):
  for old in ('rdna-r111-hip-4b','rdna-r120-hip-4b','upstream-master-4b','prism-head-4b','chimera-062-mmb-on'):
   self.assertNotIn(old,mod.LATEST_ONLY_CANDIDATES)

if __name__=='__main__':unittest.main(verbosity=2)
