#!/usr/bin/env python3
import json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class LatestUpstreamVulkan(unittest.TestCase):
 def test_current_source_and_isolation(self):
  s=(R/'.github/workflows/lab-latest-upstream-masterf64a-vulkan.yml').read_text()
  pin=json.loads((R/'tools/benchmarks/latest_engine_sources_20261023.json').read_text())['github_repositories']['upstream']
  self.assertEqual(pin['commit'],'f64a49819ccbf67a710f9a1927080e25775651ef')
  for required in ('upstream-master-4b','-DGGML_VULKAN=ON','latest-upstream-masterf64a-vulkan','NOT_GPU_QUALIFIED.txt','git ls-remote','sha256sum'):
   self.assertIn(required,s)
  self.assertNotIn('rdna-r114',s)
if __name__=='__main__':unittest.main(verbosity=2)
